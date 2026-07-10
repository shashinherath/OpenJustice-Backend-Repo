from datetime import datetime, timedelta, timezone
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.llm_log_repository import ILLMLogRepository
from app.presentation.schemas.admin_schema import AdminCostAnalyticsResponse, CostDriver, TwilioItem, DailyCostPoint, DailyModelCostPoint

class AdminCostAnalyticsService:
    def __init__(self, chat_repo: IChatRepository, llm_log_repo: ILLMLogRepository):
        self.chat_repo = chat_repo
        self.llm_log_repo = llm_log_repo

    async def get_cost_analytics(self) -> AdminCostAnalyticsResponse:
        from sqlalchemy import select, func, cast, Date, and_, case
        from app.infrastructure.models.llm_request import LLMRequest
        from app.infrastructure.models.audio_request import AudioRequest
        from app.infrastructure.models.message import Message
        from app.infrastructure.models.conversation import Conversation

        session = getattr(self.chat_repo, 'db', None)
        if not session:
            return AdminCostAnalyticsResponse(cost_drivers=[], twilio_items=[], daily_costs=[], daily_model_costs=[])

        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        def calc_trend(current: float, previous: float) -> str:
            if previous == 0:
                if current > 0:
                    return "+100%"
                return "+0%"
            change = ((current - previous) / previous) * 100
            sign = "+" if change > 0 else ""
            return f"{sign}{round(change)}%"

        cost_drivers = []
        
        # 1. LLM Costs dynamically from models
        llm_query = select(
            LLMRequest.model_name,
            func.sum(LLMRequest.prompt_tokens).label("prompt"),
            func.sum(LLMRequest.completion_tokens).label("completion"),
            func.sum(LLMRequest.total_tokens).label("total"),
            func.sum(
                case(
                    (LLMRequest.created_at >= thirty_days_ago, LLMRequest.prompt_tokens + LLMRequest.completion_tokens), 
                    else_=0
                )
            ).label("recent_usage"),
            func.sum(
                case(
                    (and_(LLMRequest.created_at >= sixty_days_ago, LLMRequest.created_at < thirty_days_ago), LLMRequest.prompt_tokens + LLMRequest.completion_tokens), 
                    else_=0
                )
            ).label("previous_usage"),
        ).group_by(LLMRequest.model_name)
        
        llm_res = await session.execute(llm_query)
        llm_data = llm_res.fetchall()
        
        # Rates per 1M tokens based on standard pricing
        model_rates = {
            "gpt-4o": {"prompt": 2.50, "completion": 10.00},
            "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
            "text-embedding-3-large": {"total": 0.13},
            "text-embedding-3-small": {"total": 0.02},
            "text-embedding-ada-002": {"total": 0.10},
        }

        for row in llm_data:
            model = row.model_name or "unknown-model"
            prompt = row.prompt or 0
            completion = row.completion or 0
            total = row.total or 0
            
            recent_usage = row.recent_usage or 0
            previous_usage = row.previous_usage or 0
            trend_str = calc_trend(float(recent_usage), float(previous_usage))
            
            rate = model_rates.get(model, {"prompt": 2.50, "completion": 10.0, "total": 0.13})
            
            if "embedding" in model.lower():
                cost = (total / 1_000_000) * rate.get("total", 0.02)
                cost_drivers.append(CostDriver(
                    key=f"emb_{model}",
                    title="Vector Embeddings",
                    model=model,
                    unit="embedded tokens",
                    usage=total,
                    estimatedCost=round(cost, 3),
                    trend=trend_str,
                    detail="RAG indexing and semantic search",
                    colorClass="bg-emerald-400"
                ))
            else:
                cost = ((prompt / 1_000_000) * rate.get("prompt", 2.50)) + ((completion / 1_000_000) * rate.get("completion", 10.0))
                cost_drivers.append(CostDriver(
                    key=f"llm_{model}",
                    title="Language Models",
                    model=model,
                    unit="input/output tokens",
                    usage=prompt + completion,
                    estimatedCost=round(cost, 3),
                    trend=trend_str,
                    detail="Text generation and reasoning",
                    colorClass="bg-cyan-400"
                ))

        # 2. Audio Costs
        audio_query = select(
            AudioRequest.audio_type,
            func.sum(AudioRequest.duration_seconds).label("duration"),
            func.sum(AudioRequest.characters_generated).label("chars"),
            func.sum(
                case((AudioRequest.created_at >= thirty_days_ago, AudioRequest.duration_seconds), else_=0)
            ).label("recent_dur"),
            func.sum(
                case((and_(AudioRequest.created_at >= sixty_days_ago, AudioRequest.created_at < thirty_days_ago), AudioRequest.duration_seconds), else_=0)
            ).label("prev_dur")
        ).group_by(AudioRequest.audio_type)
        
        audio_res = await session.execute(audio_query)
        audio_data = audio_res.fetchall()
        
        for row in audio_data:
            atype = (row.audio_type or "unknown").lower()
            dur = row.duration or 0
            chars = row.chars or 0
            recent_dur = row.recent_dur or 0
            prev_dur = row.prev_dur or 0
            trend_str = calc_trend(float(recent_dur), float(prev_dur))
            
            if atype == 'stt':
                minutes = dur / 60
                cost = minutes * 0.003  # $0.003 / minute
                cost_drivers.append(CostDriver(
                    key="stt",
                    title="Speech-to-Text",
                    model="gpt-4o-mini-transcribe",
                    unit="minutes transcribed",
                    usage=int(minutes),
                    estimatedCost=round(cost, 3),
                    trend=trend_str,
                    detail="Audio uploads converted into text",
                    colorClass="bg-amber-400"
                ))
            elif atype == 'tts':
                actual_chars = chars if chars > 0 else int(dur * 15)
                minutes = dur / 60
                cost = ((actual_chars / 1_000_000) * 0.60) + (minutes * 0.015)
                cost_drivers.append(CostDriver(
                    key="tts",
                    title="Text-to-Speech",
                    model="gpt-4o-mini-tts",
                    unit="characters / minutes",
                    usage=actual_chars,
                    estimatedCost=round(cost, 3),
                    trend=trend_str,
                    detail="Audio responses generated for voice",
                    colorClass="bg-rose-400"
                ))

        if not cost_drivers:
             cost_drivers = [
                 CostDriver(key="llm", title="Language Models", model="gpt-4o-mini", unit="input/output tokens", usage=0, estimatedCost=0.0, trend="+0%", detail="Primary text generation", colorClass="bg-cyan-400")
             ]

        # 3. Twilio Costs
        wa_inbound_query = select(func.count(Message.id)).select_from(Conversation).join(Message, Message.conversation_id == Conversation.id).where(and_(Conversation.channel == 'whatsapp', Message.sender == 'user'))
        wa_outbound_query = select(func.count(Message.id)).select_from(Conversation).join(Message, Message.conversation_id == Conversation.id).where(and_(Conversation.channel == 'whatsapp', Message.sender != 'user'))
        
        wa_inbound_res = await session.execute(wa_inbound_query)
        wa_outbound_res = await session.execute(wa_outbound_query)
        
        wa_inbound = wa_inbound_res.scalar() or 0
        wa_outbound = wa_outbound_res.scalar() or 0
        
        inbound_cost = wa_inbound * 0.005
        outbound_cost = wa_outbound * 0.005
        
        # Estimate failures (~2% of outbound messages) and Meta templates (~10% of outbound messages)
        estimated_failures = int(wa_outbound * 0.02)
        failures_cost = estimated_failures * 0.001
        
        estimated_templates = int(wa_outbound * 0.10)
        meta_template_cost = estimated_templates * 0.05
        
        twilio_items = [
            TwilioItem(label="Inbound messages", value=wa_inbound, cost=round(inbound_cost, 3), note="User messages ($0.005/msg)"),
            TwilioItem(label="Outbound messages", value=wa_outbound, cost=round(outbound_cost, 3), note="System replies ($0.005/msg)"),
            TwilioItem(label="Meta Template fees (Est.)", value=estimated_templates, cost=round(meta_template_cost, 3), note="Marketing/Utility convs"),
            TwilioItem(label="Failed messages (Est.)", value=estimated_failures, cost=round(failures_cost, 3), note="Processing fee ($0.001/msg)")
        ]

        # 4. Daily Costs
        seven_days_ago = now - timedelta(days=7)
        
        daily_llm_query = select(
            cast(LLMRequest.created_at, Date).label("date"),
            LLMRequest.model_name,
            func.sum(LLMRequest.prompt_tokens).label("prompt"),
            func.sum(LLMRequest.completion_tokens).label("completion"),
            func.sum(LLMRequest.total_tokens).label("total")
        ).where(LLMRequest.created_at >= seven_days_ago).group_by(cast(LLMRequest.created_at, Date), LLMRequest.model_name)
        
        daily_llm_res = await session.execute(daily_llm_query)
        daily_llm_data = daily_llm_res.fetchall()
        
        daily_audio_query = select(
            cast(AudioRequest.created_at, Date).label("date"),
            AudioRequest.audio_type,
            func.sum(AudioRequest.duration_seconds).label("duration"),
            func.sum(AudioRequest.characters_generated).label("chars")
        ).where(AudioRequest.created_at >= seven_days_ago).group_by(cast(AudioRequest.created_at, Date), AudioRequest.audio_type)
        
        daily_audio_res = await session.execute(daily_audio_query)
        daily_audio_data = daily_audio_res.fetchall()
        
        daily_wa_query = select(
            cast(Message.created_at, Date).label("date"),
            Message.sender,
            func.count(Message.id).label("count")
        ).select_from(Conversation).join(Message, Message.conversation_id == Conversation.id)\
        .where(and_(Conversation.channel == 'whatsapp', Message.created_at >= seven_days_ago))\
        .group_by(cast(Message.created_at, Date), Message.sender)
        
        daily_wa_res = await session.execute(daily_wa_query)
        daily_wa_data = daily_wa_res.fetchall()

        day_costs = {}
        day_model_costs = {}
        for i in range(6, -1, -1):
            d = (now - timedelta(days=i)).date()
            day_costs[d] = {"openAi": 0.0, "twilio": 0.0}
            day_model_costs[d] = {"llm": 0.0, "embedding": 0.0, "stt": 0.0, "tts": 0.0}
            
        for row in daily_llm_data:
            if row.date in day_costs:
                model = row.model_name or "gpt-4o"
                rate = model_rates.get(model, {"prompt": 2.50, "completion": 10.00, "total": 0.13})
                if "embedding" in model.lower():
                    cost = ((row.total or 0) / 1_000_000) * rate.get("total", 0.02)
                    day_model_costs[row.date]["embedding"] += cost
                else:
                    cost = (((row.prompt or 0) / 1_000_000) * rate.get("prompt", 2.50)) + (((row.completion or 0) / 1_000_000) * rate.get("completion", 10.00))
                    day_model_costs[row.date]["llm"] += cost
                day_costs[row.date]["openAi"] += cost
                
        for row in daily_audio_data:
             if row.date in day_costs:
                 atype = (row.audio_type or "unknown").lower()
                 dur = row.duration or 0
                 chars = row.chars or 0
                 if atype == 'stt':
                     cost = (dur / 60) * 0.003
                     day_model_costs[row.date]["stt"] += cost
                 elif atype == 'tts':
                     actual_chars = chars if chars > 0 else int(dur * 15)
                     cost = ((actual_chars / 1_000_000) * 0.60) + ((dur / 60) * 0.015)
                     day_model_costs[row.date]["tts"] += cost
                 else:
                     cost = 0
                 day_costs[row.date]["openAi"] += cost
                 
        for row in daily_wa_data:
            if row.date in day_costs:
                count = row.count or 0
                is_outbound = (row.sender != 'user')
                cost = count * 0.005
                if is_outbound:
                    cost += (count * 0.10 * 0.05)
                    cost += (count * 0.02 * 0.001)
                day_costs[row.date]["twilio"] += cost

        daily_costs = []
        daily_model_costs = []
        for d in sorted(day_costs.keys()):
            day_str = d.strftime("%a")
            daily_costs.append(DailyCostPoint(
                day=day_str,
                openAi=round(day_costs[d]["openAi"], 3),
                twilio=round(day_costs[d]["twilio"], 3)
            ))
            daily_model_costs.append(DailyModelCostPoint(
                day=day_str,
                llm=round(day_model_costs[d]["llm"], 3),
                embedding=round(day_model_costs[d]["embedding"], 3),
                stt=round(day_model_costs[d]["stt"], 3),
                tts=round(day_model_costs[d]["tts"], 3)
            ))

        return AdminCostAnalyticsResponse(
            cost_drivers=cost_drivers,
            twilio_items=twilio_items,
            daily_costs=daily_costs,
            daily_model_costs=daily_model_costs
        )
