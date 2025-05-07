from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config import templates
from app.database.db import get_db
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.routes.auth import get_current_user, get_current_user_ws

router = APIRouter()

# ✏️ История чата (HTTP)
@router.get("/chat/history", response_class=JSONResponse)
async def chat_history(
    peer_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(403, "Требуется авторизация")
    svc = ChatService(db)
    data = await svc.get_history(current_user.id, peer_id)
    return data

# ✏️ Страница чата
@router.get("/chat", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    peer_id: UUID = Query(...),              # теперь обязателен
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(403, "Требуется авторизация")
    peer = await UserService(db).get_user_by_id(peer_id)
    if not peer:
        raise HTTPException(404, "Пользователь не найден")
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "current_user": current_user,
            "initial_peer_id": str(peer.id),
            "initial_peer_name": peer.full_name
        }
    )

# WebSocket-endpoint
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active_connections[user_id] = ws

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def broadcast(self, msg: dict, users: list[str]):
        for uid in users:
            ws = self.active_connections.get(uid)
            if ws:
                await ws.send_json(msg)

manager = ConnectionManager()

@router.websocket("/ws/chat/{peer_id}")
async def websocket_chat(
    websocket: WebSocket,
    peer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_ws)
):
    me_id = current_user.id
    # проверяем, что peer существует
    peer = await UserService(db).get_user_by_id(peer_id)
    if not peer:
        await websocket.close(code=1003)
        return

    await manager.connect(str(me_id), websocket)
    svc = ChatService(db)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            recv = UUID(data.get("receiver_id", ""))
            if not content or recv != peer_id:
                continue

            # сохраняем и рассылаем
            msg = await svc.save_message(me_id, peer_id, content)
            await manager.broadcast(msg, [str(me_id), str(peer_id)])
    except WebSocketDisconnect:
        manager.disconnect(str(me_id))


@router.get("/conversations", response_class=HTMLResponse)
async def conversations_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(403, "Требуется авторизация")
    convos = await ChatService(db).get_conversations(current_user.id)
    return templates.TemplateResponse(
        "conversations.html",
        {"request": request, "current_user": current_user, "conversations": convos}
    )