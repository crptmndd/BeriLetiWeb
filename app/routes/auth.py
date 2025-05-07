from fastapi import APIRouter, Depends, HTTPException, Request, status, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.forms import RegistrationForm, LoginForm
from app.services.user_service import UserService
from app.services.phone_verification_service import PhoneVerificationService
from app.schemas import UserCreate, UserLogin
from app.config import templates
from app.services.csrf_service import CSRFService
from app.services.redis_service import RedisService
# from app.services.hash_service import HashService
from uuid import UUID

router = APIRouter()



async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        service = UserService(db)
        user = await service.get_user_by_id(user_id)
        return user
    return None

async def get_current_user_ws(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    session = websocket.session  # SessionMiddleware прокидывает session и сюда
    user_id = session.get("user_id")
    if not user_id:
        await websocket.close(code=1008)
        return
    user = await UserService(db).get_user_by_id(UUID(user_id))
    if not user:
        await websocket.close(code=1008)
        return
    return user


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    csrf_token = CSRFService.generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    form = RegistrationForm(request=request)
    return templates.TemplateResponse("register.html", {"request": request, "form": form, "csrf_token": csrf_token})


@router.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    session_token = request.session.get("csrf_token")
    form_token = form_data.get("csrf_token")
    CSRFService.validate_csrf_token(session_token, form_token)  
    form = await RegistrationForm.from_formdata(request)
    if await form.validate_on_submit():
        user_data = UserCreate(
            phone_number=form.phone_number.data,
            full_name=form.full_name.data,
            password=form.password.data
        )
        
        service = UserService(db)
        existing_user = await service.get_user_by_phone(user_data.phone_number)
        if existing_user:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "form": form, "csrf_token": request.session.get("csrf_token"), "error": "Номер телефона уже зарегистрирован"}
            )
        
        key = f"pending_user: {user_data.phone_number}"
        
        redis_service = RedisService()
        
        hashed_password = await service.hash_service.hash_password(user_data.password)
        user_data.password = hashed_password 
        
        verification_service = PhoneVerificationService()
        ver_code = verification_service.generate_verification_code()
        
        await redis_service.set(key, {
            "user_data": user_data.model_dump(),
            "verification_code": str(ver_code)
        }, ex=300)
    
        await verification_service.send_sms_code(phone_number=form.phone_number.data, code=ver_code)
        request.session["pending_phone"] = user_data.phone_number

        return RedirectResponse(url='/verify_phone', status_code=301)

    return templates.TemplateResponse("register.html", {"request": request, "form": form, "csrf_token": request.session.get("csrf_token")})


@router.get("/verify_phone", response_class=HTMLResponse)
async def verify_phone_get(request: Request):
    phone_number = request.session.get("pending_phone")
    if not phone_number:
        return RedirectResponse(url="/register", status_code=302)
    return templates.TemplateResponse("verify_phone.html", {"request": request, "phone_number": phone_number})


@router.post("/verify_phone", response_class=HTMLResponse)
async def verify_phone_post(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    code_parts = [form_data.get(f'code{i}', '') for i in range(1, 5)]
    entered_code = ''.join(code_parts)
    
    phone_number = request.session.get("pending_phone")
    if not phone_number:
        return templates.TemplateResponse(
            "verify_phone.html",
            {"request": request, "error": "Сессия истекла, повторите регистрацию"}
        )
    
    redis_service = RedisService()
    key = f"pending_user: {phone_number}"
    pending_data = await redis_service.get(key)
    
    if pending_data and entered_code == pending_data["verification_code"]:
        user_data = UserCreate(**pending_data["user_data"])
        service = UserService(db)
        new_user = await service.create_user(user_data)
        await redis_service.delete(key)  # Очищаем Redis
        request.session["user_id"] = str(new_user.id)
        if "pending_phone" in request.session:
            del request.session["pending_phone"]
        return templates.TemplateResponse(
            "main.html",
            {"request": request, "current_user": new_user, "success": "Регистрация прошла успешно"}
        )
    return templates.TemplateResponse(
        "verify_phone.html",
        {"request": request, "phone_number": phone_number, "error": "Неверный код или данные устарели"}
    )
    
    
@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    csrf_token = CSRFService.generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    form = LoginForm(request=request)
    return templates.TemplateResponse("login.html", {"request": request, "form": form, "csrf_token": csrf_token})


@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, db: AsyncSession = Depends(get_db)):
    form_data = await request.form()
    session_token = request.session.get("csrf_token")
    form_token = form_data.get("csrf_token")
    CSRFService.validate_csrf_token(session_token, form_token)
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