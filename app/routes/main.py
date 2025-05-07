from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.forms import CreateTripForm, TripQueryForm
from app.schemas import TripCreate
from app.services.trip_service import TripService
from app.routes.auth import get_current_user
from datetime import date
from app.config import templates
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import Trip, Reviews

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
    form = await TripQueryForm.from_formdata(request)
    current_user = await get_current_user(request, db)

    if form.validate():
        # собираем параметры
        fl = form.from_location.data
        tl = form.to_location.data
        dd = form.departure_date.data.strftime("%Y-%m-%d")
        # редирект на новую страницу результатов
        return RedirectResponse(
            url=f"/search_results?from_location={fl}&to_location={tl}&departure_date={dd}",
            status_code=302
        )
    # при ошибке валидации — обратно в форму
    return templates.TemplateResponse(
        "search_trip.html",
        {"request": request, "current_user": current_user, "form": form}
    )
    
    
@router.get("/search_results", response_class=HTMLResponse)
async def search_results(
    request: Request,
    from_location: str = Query(...),
    to_location: str = Query(...),
    departure_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(403, "Требуется авторизация")

    # 1) Получаем поездки + профиль попутчика
    stmt = (
        select(Trip)
        .options(selectinload(Trip.user))  # eager load user
        .where(
            Trip.from_location.ilike(f"%{from_location}%"),
            Trip.to_location.ilike(f"%{to_location}%"),
            Trip.departure_date == departure_date
        )
        .order_by(Trip.departure_date)
    )
    res = await db.execute(stmt)
    trips = res.scalars().all()

    user_ids = [t.user_id for t in trips]
    if user_ids:
        # 2) Считаем число поездок каждого попутчика
        trips_cnt_stmt = (
            select(Trip.user_id, func.count(Trip.id))
            .where(Trip.user_id.in_(user_ids))
            .group_by(Trip.user_id)
        )
        cnt_res = await db.execute(trips_cnt_stmt)
        trips_count = dict(cnt_res.all())

        # 3) Считаем жалобы (reviews) на каждого
        rev_cnt_stmt = (
            select(Reviews.reviewee_id, func.count(Reviews.id))
            .where(Reviews.reviewee_id.in_(user_ids))
            .group_by(Reviews.reviewee_id)
        )
        rev_res = await db.execute(rev_cnt_stmt)
        reviews_count = dict(rev_res.all())
    else:
        trips_count = reviews_count = {}

    # 4) Формируем список простых dict’ов для шаблона
    date_str = departure_date.strftime("%d.%m.%Y")
    
    trips_data = []
    for t in trips:
        u = t.user
        trips_data.append({
            "id": str(t.id),
            "user_id": str(u.id),                # ← UUID попутчика
            "from_location": t.from_location,
            "to_location": t.to_location,
            "departure_date": t.departure_date,
            "max_weight": t.max_weight,
            "price": t.price,
            "user_full_name": u.full_name,
            "user_rating": u.rating,
            "user_avatar": u.avatar,
            "trips_count": trips_count.get(u.id, 0),
            "complaints_count": reviews_count.get(u.id, 0)
        })

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "current_user": current_user,
            "trips": trips_data,
            "count": len(trips_data),
            "from_location": from_location,
            "to_location": to_location,
            "departure_date": date_str
        }
    )