# app/routes/chat.py
from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import templates
from app.database.db import get_db
from app.services.user_service import UserService
from app.models import Message as MessageModel
from datetime import datetime
from app.routes.auth import get_current_user  # ваш dependency
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter()

class MessageSchema(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return HTMLResponse("Доступ запрещён", status_code=403)
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "current_user": current_user}
    )

@router.get("/api/chat/history", response_model=List[MessageSchema])
async def chat_history(
    peer_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # проверяем существование peer
    service = UserService(db)
    peer = await service.get_user_by_id(peer_id)
    if not peer:
        raise HTTPException(404, "Пользователь не найден")

    stmt = select(MessageModel).where(
        or_(
            and_(
                MessageModel.sender_id == current_user.id,
                MessageModel.receiver_id == peer.id
            ),
            and_(
                MessageModel.sender_id == peer.id,
                MessageModel.receiver_id == current_user.id
            )
        )
    ).order_by(MessageModel.created_at)
    result = await db.execute(stmt)
    msgs: List[MessageModel] = result.scalars().all()

    return [
        MessageSchema(
            sender_id=str(m.sender_id),
            receiver_id=str(m.receiver_id),
            content=m.content,
            created_at=m.created_at
        )
        for m in msgs
    ]


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def send_personal(self, message: dict, user_id: str):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, message: dict, users: list[str]):
        for user in users:
            await self.send_personal(message, user)

manager = ConnectionManager()

async def get_current_user_ws(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    session = websocket.session  # если используете SessionMiddleware
    user_id = session.get("user_id")
    if not user_id:
        await websocket.close(code=1008)
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        await websocket.close(code=1008)
    return user

@router.websocket("/ws/chat/{peer_id}")
async def websocket_chat(
    websocket: WebSocket,
    peer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_ws)
):
    me_id = str(current_user.id)
    # Проверяем, есть ли peer в БД
    service = UserService(db)
    peer = await service.get_user_by_id(peer_id)
    if not peer:
        await websocket.close(code=1003)
        return

    await manager.connect(me_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            recv_id = data.get("receiver_id")
            if not content or recv_id not in {peer_id, me_id}:
                continue

            # Сохраняем сообщение
            msg = MessageModel(
                sender_id=current_user.id,
                receiver_id=peer.id,
                content=content,
                created_at=datetime.utcnow()
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            payload = {
                "sender_id": me_id,
                "receiver_id": recv_id,
                "content": content,
                "created_at": msg.created_at.isoformat()
            }
            # Шлём обоим участникам
            await manager.broadcast(payload, [me_id, peer_id])
    except WebSocketDisconnect:
        manager.disconnect(me_id)
