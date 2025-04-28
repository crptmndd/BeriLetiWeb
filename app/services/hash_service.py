from passlib.context import CryptContext

class HashService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    async def hash_password(self, password: str) -> str:
        """Хеширует пароль."""
        return self.pwd_context.hash(password)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """Проверяет пароль."""
        return self.pwd_context.verify(password, hashed_password)