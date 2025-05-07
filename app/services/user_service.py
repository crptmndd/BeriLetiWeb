from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from app.schemas import UserCreate, UserUpdate
from uuid import UUID, uuid4
from app.services.hash_service import HashService 
from fastapi import HTTPException, UploadFile
from pathlib import Path
import aiofiles
from PIL import Image
import io


ALLOWED_EXT = {".png", ".jpg", ".jpeg"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 2 MB
MAX_DIMENSION = (300, 300)         # максимальный размер аватара
JPEG_QUALITY = 85 



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
    
    async def set_avatar(self, user, upload: UploadFile):
        # 1) Проверка расширения
        ext = Path(upload.filename).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(
                status_code=400,
                detail="Неподдерживаемый формат. Разрешены: " + ", ".join(ALLOWED_EXT)
            )

        # 2) Читаем весь файл в память и проверяем размер
        content = await upload.read()
        if len(content) > MAX_AVATAR_SIZE:
            size_kb = len(content) // 1024
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой ({size_kb} КБ). Макс. {MAX_AVATAR_SIZE//(1024*1024)} МБ."
            )

        # 3) Удаляем старый аватар
        upload_dir = Path("app/static/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        if user.avatar:
            old = upload_dir / user.avatar
            if old.exists():
                old.unlink()

        # 4) Открываем через Pillow, ресайз и сжимаем
        img = Image.open(io.BytesIO(content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Используем LANCZOS вместо ANTIALIAS
        img.thumbnail(MAX_DIMENSION, Image.LANCZOS)

        buf = io.BytesIO()
        save_kwargs = {}
        if ext in (".jpg", ".jpeg"):
            save_kwargs["quality"] = JPEG_QUALITY
            save_kwargs["optimize"] = True
        img.save(buf, format=img.format or "PNG", **save_kwargs)
        data = buf.getvalue()

        # 5) Записываем на диск под новым именем
        filename = f"{uuid4()}{ext}"
        path = upload_dir / filename
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)

        # 6) Сохраняем в БД
        user.avatar = filename
        await self.db.commit()
        await self.db.refresh(user)
        return filename
    
    async def set_email(self, user_id: str, email: str):
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        user.email = email

        await self.db.commit()
