from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.user_service import UserService
from app.services.csrf_service import CSRFService
from app.database.db import get_db
from app.routes.auth import get_current_user
from app.config import templates

router = APIRouter()

@router.get("/profile")
async def profile(request: Request,
                  current_user = Depends(get_current_user)):
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "current_user": current_user}
    )

@router.get(
    "/profile/edit-photo",
    response_class=HTMLResponse,
    response_model=None,       # <- отключаем Pydantic response_model
    include_in_schema=True     # можно оставить, если хотите документацию
)
async def edit_photo_form(
    request: Request,
    current_user = Depends(get_current_user)
):
    token = CSRFService.generate_csrf_token()
    request.session["csrf_token"] = token
    return templates.TemplateResponse("edit_photo.html", {
        "request": request,
        "current_user": current_user,
        "csrf_token": token
    })


@router.post(
    "/profile/edit-photo",
    response_class=RedirectResponse,
    response_model=None         # <- и здесь отключаем
)
async def edit_photo_upload(
    request: Request,
    file: UploadFile = File(...),
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # 1) CSRF
    session_token = request.session.get("csrf_token")
    CSRFService.validate_csrf_token(session_token, csrf_token)

    # 2) Сохраняем аватар
    svc = UserService(db)
    await svc.set_avatar(current_user, file)

    # 3) Убираем токен
    request.session.pop("csrf_token", None)


    return RedirectResponse("/profile", status_code=303)
