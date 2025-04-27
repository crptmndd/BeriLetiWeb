from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.forms import RegistrationForm, LoginForm
from app.services.user_service import UserService
from app.services.verification_service import VerificationService
from app.schemas import UserCreate, UserLogin
from app.config import templates
from app.services.auth_service import AuthService

router = APIRouter()


async def get_current_user(request: Request, db: AsyncSession):
    user_id = request.session.get("user_id")
    if user_id:
        service = UserService(db)
        user = await service.get_user_by_id(user_id)
        return user
    return None


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    csrf_token = AuthService.generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    form = RegistrationForm(request=request)
    return templates.TemplateResponse("register.html", {"request": request, "form": form, "csrf_token": csrf_token})

@router.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    session_token = request.session.get("csrf_token")
    form_token = form_data.get("csrf_token")
    AuthService.validate_csrf_token(session_token, form_token)  # Проверка CSRF-токен
    form = await RegistrationForm.from_formdata(request)
    if await form.validate_on_submit():
        user_data = UserCreate(
            phone_number=form.phone_number.data,
            full_name=form.full_name.data,
            birth_date=form.birth_date.data,
            password=form.password.data
        )
        
        service = UserService(db)
        existing_user = await service.get_user_by_phone(user_data.phone_number)
        if existing_user:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "form": form, "csrf_token": request.session.get("csrf_token"), "error": "Номер телефона уже зарегистрирован"}
            )
            
        request.session['pending_user'] = {
            'phone_number': form.phone_number.data,
            "full_name": form.full_name.data,
            "birth_date": str(form.birth_date.data),
            "password": form.password.data
        }
        
        verification_service = VerificationService()

        ver_code = verification_service.generate_verification_code()
        request.session["verification_code"] = str(ver_code)

        await verification_service.send_sms_code(phone_number=form.phone_number.data, code=ver_code)

        return RedirectResponse(url='/verify_phone', status_code=301)

    return templates.TemplateResponse("register.html", {"request": request, "form": form, "csrf_token": request.session.get("csrf_token")})

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    csrf_token = AuthService.generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    form = LoginForm(request=request)
    return templates.TemplateResponse("login.html", {"request": request, "form": form, "csrf_token": csrf_token})

@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    session_token = request.session.get("csrf_token")
    form_token = form_data.get("csrf_token")
    AuthService.validate_csrf_token(session_token, form_token)
    form = await LoginForm.from_formdata(request)
    if await form.validate_on_submit():
        service = UserService(db)
        user = await service.login_user(form.phone_number.data, form.password.data)
        if user:
            request.session["user_id"] = str(user.id)
            return templates.TemplateResponse(
                "main.html",
                {"request": request, "current_user": user, "success": "Вход выполнен успешно"}
            )
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "form": form, "csrf_token": request.session.get("csrf_token"), "error": "Неверные данные"}
        )
    return templates.TemplateResponse("login.html", {"request": request, "form": form, "csrf_token": request.session.get("csrf_token")})


@router.get("/logout")
async def logout(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
    return RedirectResponse(url="/", status_code=302)


@router.get("/verify_phone", response_class=HTMLResponse)
async def verify_phone_get(request: Request):
    return templates.TemplateResponse("verify_phone.html", {"request": request})

@router.post("/verify_phone", response_class=HTMLResponse)
async def verify_phone_post(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    code_parts = [form_data.get(f'code{i}', '') for i in range(1, 5)]
    entered_code = ''.join(code_parts)
    session_code = request.session.get('verification_code')
    if entered_code == session_code:
        user_data = UserCreate(**request.session.get('pending_user'))
        print(user_data)
        service = UserService(db)
        new_user = await service.create_user(user_data)
        request.session["user_id"] = str(new_user.id)
        del request.session['verification_code']
        del request.session['pending_user']
        return templates.TemplateResponse(
            "main.html",
            {"request": request, "current_user": new_user, "success": "Регистрация прошла успешно"}
        )
    return templates.TemplateResponse(
        "verify_phone.html",
        {"request": request, "error": "Неверный код"}
    )