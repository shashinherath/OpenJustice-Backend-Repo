from datetime import datetime, timedelta
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.llm_log_repository import ILLMLogRepository
from app.presentation.schemas.admin_schema import AdminCostAnalyticsResponse, CostDriver, TwilioItem, DailyCostPoint

class AdminCostAnalyticsService:
    def __init__(self, chat_repo: IChatRepository, llm_log_repo: ILLMLogRepository):
        self.chat_repo = chat_repo
        self.llm_log_repo = llm_log_repo

    async def get_cost_analytics(self) -> AdminCostAnalyticsResponse:
        from sqlalchemy import select, func, cast, Date
        from app.infrastructure.models.llm_request import LLMRequest
        from app.infrastructure.models.audio_request import AudioRequest
        from app.infrastructure.models.message import Message
        from app.infrastructure.models.conversation import Conversation

        session = getattr(self.chat_repo, 'db', None)
        if not session:
            return AdminCostAnalyticsResponse(cost_drivers=[], twilio_items=[], daily_costs=[])

        cost_drivers = []
        
        # 1. LLM Costs dynamically from models
        llm_query = select(
            LLMRequest.model_name,
            func.sum(LLMRequest.prompt_tokens).label("prompt"),
            func.sum(LLMRequest.completion_tokens).label("completion"),
            func.sum(LLMRequest.total_tokens).label("total")
        ).group_by(LLMRequest.model_name)
        
        llm_res = await session.execute(llm_query)
        llm_data = llm_res.fetchall()
        
        # Rates per 1M tokens
        model_rates = {
            "gpt-4o": {"prompt": 5.0, "completion": 15.0},
            "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
            "gpt-4": {"prompt": 30.0, "completion": 60.0},
            "text-embedding-3-small": {"total": 0.02},
            "text-embedding-ada-002": {"total": 0.10},
        }

        for row in llm_data:
            model = row.model_name or "unknown-model"
            prompt = row.prompt or 0
            completion = row.completion or 0
            total = row.total or 0
            
            rate = model_rates.get(model, {"prompt": 1.0, "completion": 1.0, "total": 1.0})
            
            if "embedding" in model.lower():
                cost = (total / 1_000_000) * rate.get("total", 0.02)
                cost_drivers.append(CostDriver(
                    key=f"emb_{model}",
                    title="Vector Embeddings",
                    model=model,
                    unit="embedded tokens",
                    usage=total,
                    estimatedCost=round(cost, 2),
                    trend="+0%",
                    detail="RAG indexing and semantic search",
                    colorClass="bg-emerald-400"
                ))
            else:
                cost = ((prompt / 1_000_000) * rate.get("prompt", 1.0)) + ((completion / 1_000_000) * rate.get("completion", 1.0))
                cost_drivers.append(CostDriver(
                    key=f"llm_{model}",
                    title="Language Models",
                    model=model,
                    unit="input/output tokens",
                    usage=prompt + completion,
                    estimatedCost=round(cost, 2),
                    trend="+0%",
                    detail="Text generation and reasoning",
                    colorClass="bg-cyan-400"
                ))

        # 2. Audio Costs
        audio_query = select(
            AudioRequest.audio_type,
            func.sum(AudioRequest.duration_seconds).label("duration"),
            func.sum(AudioRequest.characters_generated).label("chars")
        ).group_by(AudioRequest.audio_type)
        
        audio_res = await session.execute(audio_query)
        audio_data = audio_res.fetchall()
        
        for row in audio_data:
            atype = (row.audio_type or "unknown").lower()
            dur = row.duration or 0
            chars = row.chars or 0
            
            if atype == 'stt':
                minutes = dur / 60
                cost = minutes * 0.006  # whisper standard rate
                cost_drivers.append(CostDriver(
                    key="stt",
                    title="Speech-to-Text",
                    model="whisper-1",
                    unit="minutes transcribed",
                    usage=int(minutes),
                    estimatedCost=round(cost, 2),
                    trend="+0%",
                    detail="Audio uploads converted into text",
                    colorClass="bg-amber-400"
                ))
            elif atype == 'tts':
                # Use chars if tracked, else estimate 15 chars per sec
                actual_chars = chars if chars > 0 else int(dur * 15)
                cost = (actual_chars / 1000) * 0.015  # standard tts
                cost_drivers.append(CostDriver(
                    key="tts",
                    title="Text-to-Speech",
                    model="tts-1 / alloy",
                    unit="characters generated",
                    usage=actual_chars,
                    estimatedCost=round(cost, 2),
                    trend="+0%",
                    detail="Audio responses generated for voice",
                    colorClass="bg-rose-400"
                ))

        # Ensure we have at least defaults if db is completely empty
        if not cost_drivers:
             cost_drivers = [
                 CostDriver(key="llm", title="Language Models", model="gpt-4o", unit="input/output tokens", usage=0, estimatedCost=0.0, trend="+0%", detail="Primary text generation", colorClass="bg-cyan-400")
             ]

        # 3. Twilio Costs
        wa_res = await session.execute(
            select(func.count(Message.id))
            .select_from(Conversation)
            .join(Message, Message.conversation_id == Conversation.id)
            .where(Conversation.channel == 'whatsapp')
        )
        wa_messages = wa_res.scalar() or 0
        wa_cost = wa_messages * 0.006 # standard wa message
        
        twilio_items = [
            TwilioItem(label="WhatsApp messages", value=wa_messages, cost=round(wa_cost, 2), note="Per-message send/receive fees"),
            TwilioItem(label="Monthly phone number", value=1, cost=1.5, note="Recurring line rental"),
            TwilioItem(label="Delivery retries", value=int(wa_messages * 0.05), cost=round(wa_messages * 0.05 * 0.006, 2), note="Retry and network fallback traffic")
        ]

        # 4. Daily Costs
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_llm_query = select(
            cast(LLMRequest.created_at, Date).label("date"),
            LLMRequest.model_name,
            func.sum(LLMRequest.prompt_tokens).label("prompt"),
            func.sum(LLMRequest.completion_tokens).label("completion"),
            func.sum(LLMRequest.total_tokens).label("total")
        ).where(LLMRequest.created_at >= seven_days_ago).group_by(cast(LLMRequest.created_at, Date), LLMRequest.model_name)
        
        daily_llm_res = await session.execute(daily_llm_query)
        daily_llm_data = daily_llm_res.fetchall()
        
        daily_wa_query = select(
            cast(Message.created_at, Date).label("date"),
            func.count(Message.id).label("count")
        ).select_from(Conversation).join(Message, Message.conversation_id == Conversation.id)\
        .where(Conversation.channel == 'whatsapp', Message.created_at >= seven_days_ago)\
        .group_by(cast(Message.created_at, Date))
        
        daily_wa_res = await session.execute(daily_wa_query)
        daily_wa_data = daily_wa_res.fetchall()

        day_costs = {}
        # last 7 days init
        for i in range(6, -1, -1):
            d = (datetime.utcnow() - timedelta(days=i)).date()
            day_costs[d] = {"openAi": 0.0, "twilio": 0.0}
            
        for row in daily_llm_data:
            if row.date in day_costs:
                model = row.model_name or "gpt-4o"
                rate = model_rates.get(model, {"prompt": 1.0, "completion": 1.0, "total": 1.0})
                if "embedding" in model.lower():
                    cost = ((row.total or 0) / 1_000_000) * rate.get("total", 0.02)
                else:
                    cost = (((row.prompt or 0) / 1_000_000) * rate.get("prompt", 1.0)) + (((row.completion or 0) / 1_000_000) * rate.get("completion", 1.0))
                day_costs[row.date]["openAi"] += cost
                
        for row in daily_wa_data:
            if row.date in day_costs:
                cost = (row.count or 0) * 0.006
                day_costs[row.date]["twilio"] += cost

        daily_costs = []
        for d in sorted(day_costs.keys()):
            daily_costs.append(DailyCostPoint(
                day=d.strftime("%a"),
                openAi=round(day_costs[d]["openAi"], 2),
                twilio=round(day_costs[d]["twilio"], 2)
            ))

        return AdminCostAnalyticsResponse(
            cost_drivers=cost_drivers,
            twilio_items=twilio_items,
            daily_costs=daily_costs
        )
