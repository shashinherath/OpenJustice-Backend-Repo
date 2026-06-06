from datetime import datetime, timedelta
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.presentation.schemas.admin_schema import AdminUsageAnalyticsResponse, UsageDailyStat

class AdminUsageAnalyticsService:
    def __init__(self, chat_repo: IChatRepository, user_repo: IUserRepository):
        self.chat_repo = chat_repo
        self.user_repo = user_repo

    async def get_usage_analytics(self) -> AdminUsageAnalyticsResponse:
        from sqlalchemy import select, func, text, cast, Date, extract
        from app.infrastructure.models.message import Message
        from app.infrastructure.models.user import User

        session = getattr(self.chat_repo, 'db', None)
        if not session:
            return AdminUsageAnalyticsResponse(
                total_queries_this_week=0,
                active_users=0,
                peak_hour="00:00",
                queries_per_day=[]
            )

        # 1. Queries per day for the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_query = select(
            cast(Message.created_at, Date).label("date"),
            func.count(Message.id).label("count")
        ).where(
            Message.sender == 'user',
            Message.created_at >= seven_days_ago
        ).group_by(
            cast(Message.created_at, Date)
        ).order_by(
            cast(Message.created_at, Date)
        )
        
        daily_res = await session.execute(daily_query)
        daily_stats = daily_res.fetchall()

        total_queries = 0
        queries_per_day = []
        
        for row in daily_stats:
            day_str = row.date.strftime("%a") if row.date else "Unknown"
            count = row.count or 0
            total_queries += count
            queries_per_day.append(UsageDailyStat(day=day_str, count=count))

        # Fill missing days with 0 to ensure we always return 7 days
        # We'll just generate the last 7 days and match them
        last_7_days = [(datetime.utcnow() - timedelta(days=i)).date() for i in range(6, -1, -1)]
        day_map = {row.date: row.count for row in daily_stats if row.date}
        
        filled_queries_per_day = []
        for d in last_7_days:
            filled_queries_per_day.append(
                UsageDailyStat(day=d.strftime("%a"), count=day_map.get(d, 0))
            )

        # 2. Peak Hour
        hour_query = select(
            extract('hour', Message.created_at).label("hour"),
            func.count(Message.id).label("count")
        ).where(
            Message.sender == 'user'
        ).group_by(
            extract('hour', Message.created_at)
        ).order_by(
            func.count(Message.id).desc()
        ).limit(1)
        
        hour_res = await session.execute(hour_query)
        peak_hour_row = hour_res.fetchone()
        
        peak_hour_str = "12:00"
        if peak_hour_row and peak_hour_row.hour is not None:
            peak_hour_str = f"{int(peak_hour_row.hour):02d}:00"

        # 3. Active Users
        # Can use user_repo.get_total_count() or actual query
        users_query = select(func.count(func.distinct(User.id)))
        users_res = await session.execute(users_query)
        active_users = users_res.scalar() or 0

        return AdminUsageAnalyticsResponse(
            total_queries_this_week=total_queries,
            active_users=active_users,
            peak_hour=peak_hour_str,
            queries_per_day=filled_queries_per_day
        )
