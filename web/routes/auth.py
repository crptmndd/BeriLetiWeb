from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette_wtf import StarletteForm
from passlib.context import CryptContext
from web.database.db import get_db
from web.models import User
from web.forms import RegistrationForm, LoginForm


router = APIRouter()

templates = Jinja2Templates(directory="web/templates")

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    form = RegistrationForm(request=request)
    return templates.TemplateResponse("register.html", {"request": request, "form": form})


@router.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, db: AsyncSession = Depends(get_db)):
    form = await RegistrationForm.from_formdata(request)
    
    if await form.validate_on_submit():
        existing_user = await db.execute(select(User).filter(User.phone_number == form.phone_number.data))
        if existing_user.scalar():
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "form": form, "error": "Phone number already registered"}
            )
            
        hashed_password = pwd_context.hash(form.password.data)
        
        new_user = User(
            phone_number=form.phone_number.data,
            full_name=form.full_name.data,
            birth_date=form.birth_date.data,
            password_hash=hashed_password
        )
        db.add(new_user)
        await db.commit()
        
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "form": form, "success": "Successfully registered"}
        )
    
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "form": form}
    )