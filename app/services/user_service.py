from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from app.models import User
from app.schemas import UserCreate, UserUpdate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_user_by_phone(self, phone_number: str):
        """Получить пользователя по номеру телефона."""
        
        result = await self.db.execute(select(User).filter(User.phone_number == phone_number))
        return result.scalar_one_or_none
    
    async def create_user(self, user_data: UserCreate):
        """Создать нового пользователя."""
        
        hashed_password = pwd_context.hash(user_data.password)
        new_user = User(
            phone_number=user_data.phone_number,
            full_name=user_data.full_name,
            birth_date=user_data.birth_date,
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