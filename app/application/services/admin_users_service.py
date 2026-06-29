from app.domain.interfaces.user_repository import IUserRepository
from app.domain.interfaces.audit_log_repository import IAuditLogRepository
from app.domain.interfaces.password_hasher import PasswordHasher
from app.infrastructure.models.user import User
from app.domain.exceptions import UserAlreadyExistsError

class AdminUsersService:
    def __init__(self, user_repo: IUserRepository, password_hasher: PasswordHasher = None, audit_log_repo: IAuditLogRepository = None):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.audit_log_repo = audit_log_repo

    async def create_admin_user(self, first_name: str, last_name: str, phone_number: str, email: str, password: str, current_user_id: str = None) -> dict:
        if not self.password_hasher:
            raise ValueError("Password hasher is required to create a user.")
            
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError("A user with this email already exists.")
            
        hashed_password = self.password_hasher.hash_password(password)
        user = User(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            email=email,
            hashed_password=hashed_password,
            role="admin",
            is_active=True
        )
        
        user = await self.user_repo.create(user)
        
        if self.audit_log_repo:
            from uuid import UUID
            await self.audit_log_repo.log_action(
                user_id=UUID(current_user_id) if current_user_id else None,
                action="CREATE_ADMIN_USER",
                entity="User",
                entity_id=user.id,
                metadata={"email": email}
            )

        return {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email or "",
            "phone_number": user.phone_number,
            "role": user.role,
            "status": "Active" if user.is_active else "Blocked",
            "createdDate": user.created_at.strftime("%Y-%m-%d") if user.created_at else ""
        }

    async def get_users(self, skip: int = 0, limit: int = 100, search_query: str = None, role: str = None, status: str = None) -> dict:
        users = await self.user_repo.list_users(skip=skip, limit=limit, search_query=search_query, role=role, status=status)
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
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email or "",
                "phone_number": user.phone_number,
                "role": user.role,
                "status": "Active" if user.is_active else "Blocked",
                "createdDate": user.created_at.strftime("%Y-%m-%d") if user.created_at else ""
            })

        return {
            "users": user_items,
            "total_active": total_active,
            "total_blocked": total_blocked
        }

    async def update_user_status(self, user_id: str, is_active: bool, current_user_id: str = None) -> dict:
        from uuid import UUID
        updated_user = await self.user_repo.update_status(UUID(user_id), is_active)
        if not updated_user:
            raise ValueError(f"User with ID {user_id} not found.")
            
        if self.audit_log_repo:
            await self.audit_log_repo.log_action(
                user_id=UUID(current_user_id) if current_user_id else None,
                action="UPDATE_USER_STATUS",
                entity="User",
                entity_id=updated_user.id,
                metadata={"is_active": is_active, "target_email": updated_user.email}
            )
            
        return {
            "id": str(updated_user.id),
            "first_name": updated_user.first_name,
            "last_name": updated_user.last_name,
            "email": updated_user.email or "",
            "phone_number": updated_user.phone_number,
            "role": updated_user.role,
            "status": "Active" if updated_user.is_active else "Blocked",
            "createdDate": updated_user.created_at.strftime("%Y-%m-%d") if updated_user.created_at else ""
        }
