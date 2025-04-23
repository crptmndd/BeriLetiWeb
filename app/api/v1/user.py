from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.services.user_service import UserService
from app.schemas import UserCreate

router = APIRouter()


@router.post("/users/", response_model=UserCreate)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    existing_user = await service.get_user_by_phone(user_data.phone_number)
    if existing_user: 
        raise HTTPException(status_code=400, detail="Phone number already registered")
    new_user = await service.create_user(user_data)
    return new_user