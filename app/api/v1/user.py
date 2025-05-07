# app/api/v1/user.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.services.user_service import UserService
from pydantic import BaseModel
from app.routes.auth import get_current_user

router = APIRouter()

# class UserInfo(BaseModel):
#     id: str
#     full_name: str

# @router.get("/get_user_by_id", response_model=UserInfo)
# async def get_user_by_id(
#     user_id: str = Query(...),
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     service = UserService(db)
#     u = await service.get_user_by_id(user_id)
#     if not u:
#         raise HTTPException(404, "Пользователь не найден")
#     return {"id": str(u.id), "full_name": u.full_name}