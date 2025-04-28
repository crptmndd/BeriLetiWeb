from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from app.schemas import UserCreate, UserUpdate
from uuid import UUID
from app.services.hash_service import HashService 


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hash_service = HashService()  
        
    async def get_user_by_phone(self, phone_number: str):
        """Получить пользователя по номеру телефона."""
        result = await self.db.execute(select(User).filter(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID):
        """Получить пользователя по ID."""
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def login_user(self, phone_number: str, password: str):
        user = await self.get_user_by_phone(phone_number)
        if user and self.hash_service.verify_password(password, user.password_hash):
            return user
        return None

    async def create_user(self, user_data: UserCreate):
        """Создать нового пользователя."""
        hashed_password = await self.hash_service.hash_password(user_data.password) 
        new_user = User(
            phone_number=user_data.phone_number,
            full_name=user_data.full_name,
            password_hash=hashed_password
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def update_user(self, user: User, user_data: UserUpdate):
        """Обновить данные пользователя."""
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.email is not None:
            user.email = user_data.email
        await self.db.commit()
        await self.db.refresh(user)
        return user
