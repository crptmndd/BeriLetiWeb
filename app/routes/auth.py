from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.forms import RegistrationForm, LoginForm
from app.services.user_service import UserService
from app.schemas import UserCreate


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


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
        exisiting_user = await service.get_user_by_phone(user_data.phone_number)
        
        if exisiting_user:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "form": form, "error": "Phone number already registered"}
            )
        await service.create_user(user_data)
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "form": form, "success": "Successfully registered"}
        ) 
        
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "form": form}
    )