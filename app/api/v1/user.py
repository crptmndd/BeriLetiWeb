# app/api/v1/user.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.services.user_service import UserService
from pydantic import BaseModel
from app.routes.auth import get_current_user

router = APIRouter()

class UserLookup(BaseModel):
    id: str
    self_id: str

@router.get("/get_user_by_phone", response_model=UserLookup)
async def get_user_by_phone(phone: str = Query(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    service = UserService(db)
    peer = await service.get_user_by_phone(phone)
    if not peer:
        raise HTTPException(404, "Пользователь не найден")
    return {"id": str(peer.id), "self_id": str(current_user.id)}
