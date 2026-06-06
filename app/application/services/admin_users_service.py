from app.domain.interfaces.user_repository import IUserRepository

class AdminUsersService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def get_users(self, skip: int = 0, limit: int = 100) -> dict:
        users = await self.user_repo.list_users(skip, limit)
        user_items = []
        total_active = 0
        total_blocked = 0

        for user in users:
            if user.is_active:
                total_active += 1
            else:
                total_blocked += 1

            user_items.append({
                "id": str(user.id),
                "email": user.email or "",
                "status": "Active" if user.is_active else "Blocked",
                "createdDate": user.created_at.strftime("%Y-%m-%d") if user.created_at else ""
            })

        return {
            "users": user_items,
            "total_active": total_active,
            "total_blocked": total_blocked
        }

    async def update_user_status(self, user_id: str, is_active: bool) -> dict:
        from uuid import UUID
        updated_user = await self.user_repo.update_status(UUID(user_id), is_active)
        if not updated_user:
            raise ValueError(f"User with ID {user_id} not found.")
        return {
            "id": str(updated_user.id),
            "email": updated_user.email or "",
            "status": "Active" if updated_user.is_active else "Blocked",
            "createdDate": updated_user.created_at.strftime("%Y-%m-%d") if updated_user.created_at else ""
        }
