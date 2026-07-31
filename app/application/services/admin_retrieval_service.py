from datetime import datetime, timedelta, timezone
from app.domain.interfaces.document_repository import IDocumentRepository
from app.presentation.schemas.admin_schema import AdminRetrievalMonitoringResponse
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository


class AdminRetrievalService:
    def __init__(self, document_repo: IDocumentRepository, system_settings_repo: SystemSettingsRepository = None):
        self.document_repo = document_repo
        self.system_settings_repo = system_settings_repo

    async def get_retrieval_monitoring(self) -> AdminRetrievalMonitoringResponse:
        import re
        from sqlalchemy import select, func, cast, Date, and_
        from app.infrastructure.models.retrieval_log import RetrievalLog
        from app.infrastructure.models.retrieved_document import RetrievedDocument
        from app.infrastructure.models.document_chunk import DocumentChunk
        from app.infrastructure.models.llm_response import LLMResponse
        from app.infrastructure.models.llm_request import LLMRequest
        
        session = getattr(self.document_repo, "db", None) or getattr(self.document_repo, "session", None)
        if not session:
            return AdminRetrievalMonitoringResponse(
                metrics=[], trend_points=[], health_targets={"latencyP95": "0ms", "citationMismatchRate": "0%", "topKHitConfidence": "N/A"}, retrieval_checks=[]
            )

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # Fetch the configured similarity threshold from system settings
        sim_threshold = 0.7
        if self.system_settings_repo:
            try:
                sys_settings = await self.system_settings_repo.get_settings()
                sim_threshold = sys_settings.retrieval_similarity_threshold
            except Exception:
                pass

        # 1. Avg Similarity Score (Max per query)
        max_sim_subq = (
            select(
                RetrievedDocument.retrieval_log_id,
                func.max(RetrievedDocument.similarity_score).label("max_sim")
            )
            .join(RetrievalLog, RetrievedDocument.retrieval_log_id == RetrievalLog.id)
            .where(RetrievalLog.created_at >= seven_days_ago)
            .group_by(RetrievedDocument.retrieval_log_id)
            .subquery()
        )
        avg_sim_result = await session.execute(select(func.avg(max_sim_subq.c.max_sim)))
        avg_sim = avg_sim_result.scalar_one_or_none() or 0.0

        # 2. Avg Latency & P95
        lat_q = select(func.avg(RetrievalLog.retrieval_latency_ms)).where(RetrievalLog.created_at >= seven_days_ago)
        avg_lat_result = await session.execute(lat_q)
        avg_lat = avg_lat_result.scalar_one_or_none() or 0.0

        p95_res = await session.execute(
            select(func.percentile_cont(0.95).within_group(RetrievalLog.retrieval_latency_ms))
            .where(RetrievalLog.created_at >= seven_days_ago)
        )
        latency_p95 = p95_res.scalar_one_or_none() or 0.0

        # 3. Hit Rate metrics (MRR & Top-K) — uses configured threshold
        logs_res = await session.execute(
            select(RetrievalLog).where(RetrievalLog.created_at >= seven_days_ago)
        )
        logs = logs_res.scalars().all()
        
        total_retrievals = len(logs)
        high_conf_hits = 0
        mrr_sum = 0.0
        
        if total_retrievals > 0:
            for log in logs:
                docs_res = await session.execute(
                    select(RetrievedDocument)
                    .where(RetrievedDocument.retrieval_log_id == log.id)
                    .order_by(RetrievedDocument.similarity_score.desc())
                )
                docs = docs_res.scalars().all()
                for rank, doc in enumerate(docs, 1):
                    if doc.similarity_score and doc.similarity_score >= sim_threshold:
                        high_conf_hits += 1
                        mrr_sum += 1.0 / rank
                        break

        hit_rate = (high_conf_hits / total_retrievals * 100) if total_retrievals > 0 else 0.0
        mrr = (mrr_sum / total_retrievals) if total_retrievals > 0 else 0.0

        # Chunk hit rate: queries that returned any docs at all
        any_hit_res = await session.execute(
            select(func.count(func.distinct(RetrievalLog.id)))
            .join(RetrievedDocument)
            .where(RetrievalLog.created_at >= seven_days_ago)
        )
        any_hits = any_hit_res.scalar_one_or_none() or 0
        chunk_hit_rate = (any_hits / total_retrievals * 100) if total_retrievals > 0 else 0.0

        # Citation validity heuristic
        # Match RetrievalLog to LLMRequest by query text + time proximity (within 30 seconds)
        citation_valid_count = 0
        citation_total_count = 0
        
        try:
            recent_ret_logs = await session.execute(
                select(RetrievalLog)
                .where(RetrievalLog.created_at >= seven_days_ago)
                .order_by(RetrievalLog.created_at.desc())
                .limit(20)
            )
            recent_ret = recent_ret_logs.scalars().all()
            
            for r_log in recent_ret:
                if not r_log.query:
                    continue
                    
                # Find matching LLMRequest by same query text within a 30-second window
                llm_req_res = await session.execute(
                    select(LLMRequest).where(
                        and_(
                            LLMRequest.query == r_log.query,
                            LLMRequest.created_at >= r_log.created_at,
                            LLMRequest.created_at <= r_log.created_at + timedelta(seconds=30)
                        )
                    ).limit(1)
                )
                llm_req = llm_req_res.scalar_one_or_none()
                if not llm_req:
                    continue
                
                # Get the LLM response text
                resp_res = await session.execute(
                    select(LLMResponse).where(LLMResponse.llm_request_id == llm_req.id).limit(1)
                )
                llm_resp = resp_res.scalar_one_or_none()
                if not llm_resp or not llm_resp.response_text:
                    continue
                
                # Get the retrieved chunks for this log
                chunks_res = await session.execute(
                    select(DocumentChunk).join(
                        RetrievedDocument, RetrievedDocument.document_chunk_id == DocumentChunk.id
                    ).where(RetrievedDocument.retrieval_log_id == r_log.id)
                )
                chunks = chunks_res.scalars().all()
                if not chunks:
                    continue
                
                citation_total_count += 1
                
                # Heuristic: check if the LLM response contains significant words from retrieved chunks
                resp_words = set(re.findall(r'\w{6,}', llm_resp.response_text.lower()))
                chunk_words = set()
                for c in chunks:
                    if c.content:
                        chunk_words.update(re.findall(r'\w{6,}', c.content.lower()))
                
                overlap = resp_words.intersection(chunk_words)
                if len(overlap) >= 3:
                    citation_valid_count += 1
                    
            citation_validity = (citation_valid_count / citation_total_count * 100) if citation_total_count > 0 else 0.0
        except Exception:
            citation_validity = 0.0

        metrics = [
            {
                "label": "Avg similarity score",
                "value": f"{avg_sim:.2f}",
                "note": "Mean max-similarity across recent retrievals.",
                "tone": "cyan"
            },
            {
                "label": "Top-K accuracy",
                "value": f"{hit_rate:.1f}%",
                "note": f"Relevant chunk (>= {sim_threshold}) in first K results.",
                "tone": "emerald"
            },
            {
                "label": "Retrieval latency",
                "value": f"{int(avg_lat)}ms",
                "note": "Average time from query to vector store response.",
                "tone": "amber"
            },
            {
                "label": "Chunk hit rate",
                "value": f"{chunk_hit_rate:.1f}%",
                "note": "Queries that return at least one retrieved chunk.",
                "tone": "violet"
            },
            {
                "label": "Citation validity",
                "value": f"{citation_validity:.1f}%",
                "note": "Answer citations overlap with retrieval evidence.",
                "tone": "rose"
            }
        ]

        # 4. Trend Points (last 7 days average similarity)
        trend_query = select(
            cast(RetrievalLog.created_at, Date).label("date"),
            func.avg(max_sim_subq.c.max_sim).label("avg_sim")
        ).outerjoin(
            max_sim_subq, max_sim_subq.c.retrieval_log_id == RetrievalLog.id
        ).where(RetrievalLog.created_at >= seven_days_ago).group_by(cast(RetrievalLog.created_at, Date))
        
        trend_res = await session.execute(trend_query)
        trend_data = trend_res.fetchall()

        day_sims = {}
        for i in range(6, -1, -1):
            d = (datetime.now(timezone.utc) - timedelta(days=i)).date()
            day_sims[d] = 0.0 # true empty day filling

        for row in trend_data:
            if row.date in day_sims:
                day_sims[row.date] = (row.avg_sim or 0.0) * 100

        trend_points = []
        for d in sorted(day_sims.keys()):
            trend_points.append({
                "label": d.strftime("%a"),
                "value": int(day_sims[d])
            })

        health_targets = {
            "latencyP95": f"{int(latency_p95)}ms",
            "citationMismatchRate": f"{100.0 - citation_validity:.1f}%",
            "topKHitConfidence": "High" if hit_rate > 90 else ("Review" if hit_rate > 70 else "Degraded")
        }

        # 5. Recent Checks - Fixed N+1, with per-query citation validity
        recent_logs_q = (
            select(
                RetrievalLog,
                func.avg(RetrievedDocument.similarity_score).label("avg_sim"),
                func.count(RetrievedDocument.id).label("doc_count")
            )
            .outerjoin(RetrievedDocument, RetrievedDocument.retrieval_log_id == RetrievalLog.id)
            .group_by(RetrievalLog.id)
            .order_by(RetrievalLog.created_at.desc())
            .limit(5)
        )
        recent_logs_res = await session.execute(recent_logs_q)
        recent_logs_rows = recent_logs_res.all()

        retrieval_checks = []
        for row in recent_logs_rows:
            log = row.RetrievalLog
            log_sim = row.avg_sim or 0.0
            doc_count = row.doc_count or 0
            
            if doc_count == 0:
                status = "Fail"
            elif log_sim >= sim_threshold:
                status = "Pass"
            elif log_sim >= sim_threshold * 0.8:
                status = "Warn"
            else:
                status = "Fail"

            query_text = log.query or "General Query"
            if len(query_text) > 30:
                query_text = query_text[:27] + "..."

            # Per-query citation validity
            per_query_cit = "N/A"
            if doc_count > 0 and log.query:
                try:
                    llm_match = await session.execute(
                        select(LLMRequest).where(
                            and_(
                                LLMRequest.query == log.query,
                                LLMRequest.created_at >= log.created_at,
                                LLMRequest.created_at <= log.created_at + timedelta(seconds=30)
                            )
                        ).limit(1)
                    )
                    matched_req = llm_match.scalar_one_or_none()
                    if matched_req:
                        resp_match = await session.execute(
                            select(LLMResponse).where(LLMResponse.llm_request_id == matched_req.id).limit(1)
                        )
                        matched_resp = resp_match.scalar_one_or_none()
                        if matched_resp and matched_resp.response_text:
                            chunk_res = await session.execute(
                                select(DocumentChunk).join(
                                    RetrievedDocument, RetrievedDocument.document_chunk_id == DocumentChunk.id
                                ).where(RetrievedDocument.retrieval_log_id == log.id)
                            )
                            log_chunks = chunk_res.scalars().all()
                            if log_chunks:
                                resp_words = set(re.findall(r'\w{6,}', matched_resp.response_text.lower()))
                                chunk_words = set()
                                for c in log_chunks:
                                    if c.content:
                                        chunk_words.update(re.findall(r'\w{6,}', c.content.lower()))
                                overlap = resp_words.intersection(chunk_words)
                                per_query_cit = f"{len(overlap)} terms" if overlap else "0 terms"
                except Exception:
                    per_query_cit = "Error"

            retrieval_checks.append({
                "queryFamily": query_text,
                "topK": log.top_k or 5,
                "avgSimilarity": f"{log_sim:.2f}",
                "latency": f"{log.retrieval_latency_ms or 0}ms",
                "citationValidity": per_query_cit,
                "status": status
            })

        return AdminRetrievalMonitoringResponse(
            metrics=metrics,
            trend_points=trend_points,
            health_targets=health_targets,
            retrieval_checks=retrieval_checks
        )
