from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.auth import router as auth_router
from app.routes.main import router as main_router
from app.api.v1.user import router as user_api_router
from app.routes.profile import router as user_web_router
from app.routes.chat import router as chat_router
from starlette.middleware.sessions import SessionMiddleware
from starlette_csrf import CSRFMiddleware
from app.config import templates, SECRET_KEY
import redis
from starlette.responses import Response

app = FastAPI()

# Подключение с использованием пароля
r = redis.Redis(
    host='localhost',
    port=6379
)

class CacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "public, max-age=604800"
        return response

app.mount(
    "/static",
    CacheStaticFiles(directory="app/static", html=True),
    name="static"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=True,
    same_site="strict"
)

# Подключение маршрутов
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(user_web_router)
app.include_router(user_api_router, prefix="/api")
app.include_router(chat_router)