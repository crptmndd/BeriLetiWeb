from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.user_service import UserService
from app.services.csrf_service import CSRFService
from app.services.email_service import EmailService
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


@router.get("/profile/add-email", response_class=HTMLResponse)
async def add_email_form(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse("add_email.html", {
        "request": request,
        "current_user": current_user
    })

@router.post("/profile/add-email")
async def add_email(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1) Проверяем, что юзер залогинен
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    # 2) Сохраняем временно email в сессии, чтобы не перезаписывать сразу
    request.session["pending_email"] = email
    # 3) Генерим токен и отсылаем письмо
    token = EmailService.create_confirmation_token(str(current_user.id), email)
    await EmailService.send_confirmation_email(email, token)
    return templates.TemplateResponse("email_confirmation_sent.html", {
        "request": request, "email": email
    })

@router.get("/profile/confirm-email", response_class=HTMLResponse)
async def confirm_email(request: Request, token: str, db: AsyncSession = Depends(get_db)):
    # 1) Декодируем токен
    data = EmailService.verify_confirmation_token(token)
    user_id = data["sub"]
    email   = data["email"]
    # 2) Проверяем, что в сессии такой же pending_email
    pending = request.session.get("pending_email")
    if pending != email:
        raise HTTPException(400, "Некорректная или уже использованная ссылка")
    # 3) Привязываем email к пользователю
    svc = UserService(db)
    await svc.set_email(user_id, email)
    # 4) Чистим сессию
    request.session.pop("pending_email", None)
    return templates.TemplateResponse("email_confirmed.html", {
        "request": request, "email": email
    })