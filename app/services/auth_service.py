from secrets import token_hex
from fastapi import HTTPException

class AuthService:
    @staticmethod
    def generate_csrf_token() -> str:
        """Генерирует CSRF-токен."""
        return token_hex(16)

    @staticmethod
    def validate_csrf_token(session_token: str, form_token: str):
        """Проверяет CSRF-токен из сессии и формы."""
        if not session_token or session_token != form_token:
            raise HTTPException(status_code=403, detail="Недействительный CSRF-токен")