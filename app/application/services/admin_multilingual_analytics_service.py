from sqlalchemy import select, func
from app.domain.interfaces.chat_repository import IChatRepository
from app.presentation.schemas.admin_schema import AdminMultilingualAnalyticsResponse, LanguageStat

class AdminMultilingualAnalyticsService:
    def __init__(self, chat_repo: IChatRepository):
        self.chat_repo = chat_repo

    async def get_multilingual_analytics(self) -> AdminMultilingualAnalyticsResponse:
        from app.infrastructure.models.message import Message
        from app.infrastructure.models.translation_log import TranslationLog

        session = getattr(self.chat_repo, 'db', None)
        if not session:
            return AdminMultilingualAnalyticsResponse(
                total_queries=0,
                total_languages=0,
                translation_requests=0,
                languages=[]
            )

        # 1. Language Share
        lang_query = select(
            Message.language,
            func.count(Message.id).label("count")
        ).where(Message.sender == 'user').group_by(Message.language)
        
        lang_res = await session.execute(lang_query)
        lang_data = lang_res.fetchall()
        
        # Mapping ISO codes to full names
        lang_map = {
            "en": "English",
            "si": "Sinhala",
            "ta": "Tamil",
            "es": "Spanish",
            "fr": "French",
            "de": "German"
        }
        
        aggregated_languages = {}
        total_queries = 0
        for row in lang_data:
            code = (row.language or "en").lower()
            label = lang_map.get(code, code.upper())
            count = row.count or 0
            
            total_queries += count
            
            unique_code = code.upper()
            if unique_code in aggregated_languages:
                aggregated_languages[unique_code].count += count
            else:
                aggregated_languages[unique_code] = LanguageStat(
                    code=unique_code,
                    label=label,
                    count=count
                )
                
        languages = list(aggregated_languages.values())

        # Sort languages by count descending
        languages.sort(key=lambda x: x.count, reverse=True)

        # 2. Translation Requests
        trans_query = select(func.count(TranslationLog.id))
        trans_res = await session.execute(trans_query)
        translation_requests = trans_res.scalar() or 0

        # If completely empty, provide fallback defaults based on typical data
        if not languages:
             languages = [
                 LanguageStat(code="EN", label="English", count=0),
                 LanguageStat(code="SI", label="Sinhala", count=0),
                 LanguageStat(code="TA", label="Tamil", count=0)
             ]

        return AdminMultilingualAnalyticsResponse(
            total_queries=total_queries,
            total_languages=len([l for l in languages if l.count > 0]) or len(languages),
            translation_requests=translation_requests,
            languages=languages
        )
