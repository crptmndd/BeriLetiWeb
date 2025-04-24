from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.auth import router as auth_router
from app.routes.main import router as main_router
from app.api.v1.user import router as user_api_router
from starlette.middleware.sessions import SessionMiddleware
from app.config import SECRET_KEY

app = FastAPI()

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Подключение маршрутов
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(user_api_router, prefix="/api")