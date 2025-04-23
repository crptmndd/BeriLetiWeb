from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.auth import router as auth_router
from app.api.v1.user import router as user_api_router

app = FastAPI()

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключение маршрутов
app.include_router(auth_router, prefix="/auth")
app.include_router(user_api_router, prefix="/api")