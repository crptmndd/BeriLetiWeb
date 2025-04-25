from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.forms import CreateTripForm, TripQueryForm
from app.schemas import TripCreate
from app.services.trip_service import TripService
from app.routes.auth import get_current_user
from datetime import date
from app.config import templates

router = APIRouter()




@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("main.html", {"request": request, "current_user": current_user})
    

@router.get("/add_trip", response_class=HTMLResponse)
async def add_trip_get(request: Request, db: AsyncSession = Depends(get_db)):
    form = CreateTripForm(request=request)
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse("add_trip.html", {"request": request, "form": form, "current_user": current_user})

@router.post("/add_trip", response_class=HTMLResponse)
async def add_trip_post(request: Request, db: AsyncSession = Depends(get_db)):
    form = await CreateTripForm.from_formdata(request)
    current_user = await get_current_user(request, db)
    
    if not current_user:
        return templates.TemplateResponse(
            "add_trip.html",
            {"request": request, "form": form, "error": "Вы должны быть авторизованы для создания поездки"}
        )
    if await form.validate_on_submit():
        trip_data = TripCreate(
            from_location=form.from_location.data,
            to_location=form.to_location.data,
            departure_date=form.departure_date.data,
            max_weight=form.max_weight.data,
            price=form.price.data,
            comment=form.comment.data
        )
        
        service = TripService(db)
        try:
            await service.create_trip(trip_data, current_user.id)
            return templates.TemplateResponse(
                "main.html", 
                {"request": request, "success": "Successfully created trip"}
            )
        except Exception as e:
            print(f"Error creating trip: {e}")
            await db.rollback()
            return templates.TemplateResponse(
                "add_trip.html",
                {"request": request, "form": form, "error": "An error occurred during creating trip"}
            )
    return templates.TemplateResponse("add_trip.html", {"request": request, "form": form})


@router.get("/search_trip", response_class=HTMLResponse)
async def search_trip_get(request: Request, db: AsyncSession = Depends(get_db)):
    form = TripQueryForm(request=request)  # Создаём пустую форму для отображения
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse(
        "search_trip.html",
        {"request": request, "current_user": current_user, "form": form}
    )

@router.post("/search_trip", response_class=HTMLResponse)
async def search_trip_post(request: Request, db: AsyncSession = Depends(get_db)):
    form = await TripQueryForm.from_formdata(request)  # Извлекаем данные из POST-запроса
    current_user = await get_current_user(request, db)

    if form.validate():  # Проверяем валидность данных
        from_location = form.from_location.data
        to_location = form.to_location.data
        departure_date = form.departure_date.data

        trip_service = TripService(db)
        trips = await trip_service.search_trips(
            from_location=from_location,
            to_location=to_location,
            departure_date=departure_date
        )
        return templates.TemplateResponse(
            "search_trip.html",
            {"request": request, "current_user": current_user, "trips": trips, "form": form}
        )
    else:
        # Если данные некорректны, возвращаем форму с ошибками
        return templates.TemplateResponse(
            "search_trip.html",
            {"request": request, "current_user": current_user, "form": form}
        )
