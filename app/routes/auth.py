from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.forms import RegistrationForm, LoginForm
from app.services.user_service import UserService
from app.schemas import UserCreate


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


async def get_current_user(request: Request, db: AsyncSession):
    user_id = request.session.get("user_id")
    print(f"Session user_id: {user_id}")
    if user_id:
        service = UserService(db)
        user = await service.get_user_by_id(user_id)
        return user
    return None


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    form = RegistrationForm(request=request)
    return templates.TemplateResponse("register.html", {"request": request, "form": form})


@router.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, db: AsyncSession = Depends(get_db)):
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
        if existing_user is not None:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "form": form, "error": "Phone number already registered"}
            )
        try:
            new_user = await service.create_user(user_data)
            request.session["user_id"] = str(new_user.id)
            return templates.TemplateResponse(
                "main.html",
                {"request": request, "current_user": new_user, "success": "Successfully registered"}
            )
        except Exception as e:
            print(f"Error creating user: {e}")
            await db.rollback()
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "form": form, "error": "An error occurred during registration"}
            )
    return templates.TemplateResponse("register.html", {"request": request, "form": form})
    
    
@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    form = LoginForm(request=request)
    return templates.TemplateResponse("login.html", {"request": request, "form": form})

    
    
@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, db: AsyncSession = Depends(get_db)):
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
        else:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "form": form, "error": "Неверные данные"}
            )
    return templates.TemplateResponse("login.html", {"request": request, "form": form})


@router.get("/logout")
async def logout(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
    return RedirectResponse(url="/", status_code=302)