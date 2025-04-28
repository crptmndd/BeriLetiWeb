from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.auth import router as auth_router
from app.routes.main import router as main_router
from app.api.v1.user import router as user_api_router
from starlette.middleware.sessions import SessionMiddleware
from starlette_csrf import CSRFMiddleware
from app.config import templates, SECRET_KEY
import redis

app = FastAPI()

# Подключение с использованием пароля
r = redis.Redis(
    host='localhost',
    port=6379,
    password='123'
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=True,
    same_site="strict"
    )
# app.add_middleware(CSRFMiddleware, secret=CSRF_KEY)

# Подключение маршрутов
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(user_api_router, prefix="/api")