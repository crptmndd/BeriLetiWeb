from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.forms import CreateTripForm
from app.services.trip_service import TripService
from app.routes.auth import get_current_user

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    current_user = await get_current_user(request)
    return templates.TemplateResponse("main.html", {"request": request, "current_user": current_user})
    

@router.get("/add_trip", response_class=HTMLResponse)
async def add_trip(request: Request):
    form_data = request.form()
    print(form_data)
    return templates.TemplateResponse("main.html", {"request": request})


@router.get("/search_trip", response_class=HTMLResponse)
async def seatch_trip(request: Request):
    query_params = request.query_params
    print(query_params)
    return templates.TemplateResponse("main.html", {"request": request})