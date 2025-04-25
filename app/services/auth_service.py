from secrets import token_hex
from fastapi import Request, HTTPException

def generate_csrf_token(request: Request):
    """Генерирует CSRF-токен и сохраняет его в сессии."""
    csrf_token = token_hex(16)
    request.session["csrf_token"] = csrf_token
    return csrf_token

def validate_csrf_token(request: Request, form_data):
    """Проверяет CSRF-токен из формы и сессии."""
    session_token = request.session.get("csrf_token")
    form_token = form_data.get("csrf_token")
    print("Session token =", session_token, f"\nForm token = {form_token}")
    if not session_token or session_token != form_token:
        raise HTTPException(status_code=403, detail="Недействительный CSRF-токен")