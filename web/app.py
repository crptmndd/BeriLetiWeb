from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from web.routes import auth  # Замените на путь к вашим маршрутам

app = FastAPI()

# Подключение статических файлов (если используете CSS/JS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Подключение маршрутов
app.include_router(auth.router)