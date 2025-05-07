from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.config import templates
from app.database.db import get_db
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.trip_service import TripService
from app.services.order_service import OrderService
from app.routes.auth import get_current_user, get_current_user_ws

from app.models import Order

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
@router.get("/chat", response_class=HTMLResponse, name="chat_page")
async def chat_page(
    request: Request,
    peer_id: UUID | None     = Query(None),
    db: AsyncSession         = Depends(get_db),
    current_user             = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(403, "Требуется авторизация")

    # 1) Список всех собеседников (по истории сообщений)
    chat_svc       = ChatService(db)
    conversations  = await chat_svc.get_conversations(current_user.id)

    selected_peer = None
    order         = None
    role          = None

    # 2) Если передан peer_id — подгружаем профиль и связывающий Order
    if peer_id:
        selected_peer = await UserService(db).get_user_by_id(peer_id)
        if not selected_peer:
            raise HTTPException(404, "Пользователь не найден")

        order_svc = OrderService(db)

        # а) проверим, есть ли у нас (current_user) заказ как у customer
        order = await order_svc.get_for_users(
            customer_id=current_user.id,
            carrier_id=peer_id
        )
        if order:
            role = "customer"
        else:
            # б) иначе — может быть мы перевозчик
            order = await order_svc.get_for_users(
                customer_id=peer_id,
                carrier_id=current_user.id
            )
            if order:
                role = "carrier"

    return templates.TemplateResponse(
        "chat.html",
        {
            "request":             request,
            "current_user":        current_user,
            "conversations":       conversations,
            "initial_peer_id":     str(peer_id) if peer_id else "",
            "initial_peer_name":   selected_peer.full_name if selected_peer else "",
            "initial_peer_avatar": selected_peer.avatar    if selected_peer else "",
            "initial_peer_rating": selected_peer.rating    if selected_peer else 0,
            "order":               order,
            "role":                role
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
    
    
@router.post("/order/confirm", name="confirm_order")
async def confirm_order(
    order_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    svc = OrderService(db)
    order = await svc.db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Заказ не найден")
    # только попутчик может подтверждать
    trip = await TripService(db).get_trip_by_id(order.trip_id)
    if trip.user_id != current_user.id:
        raise HTTPException(403, "Не ваша поездка")
    await svc.update_status(order, "confirmed")
    # вернёмся в чат с заказчиком
    return RedirectResponse(f"/chat?peer_id={order.user_id}", 302)


@router.post("/order/cancel", name="cancel_order")
async def cancel_order(
    order_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    svc = OrderService(db)
    order = await svc.db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Заказ не найден")
    # кто отменяет?
    trip = await TripService(db).get_trip_by_id(order.trip_id)
    if current_user.id == order.user_id:
        new_status = "cancelled_by_customer"
        peer = trip.user_id
    elif current_user.id == trip.user_id:
        new_status = "cancelled_by_carrier"
        peer = order.user_id
    else:
        raise HTTPException(403, "Не можете отменить этот заказ")
    await svc.update_status(order, new_status)
    return RedirectResponse(f"/chat?peer_id={peer}", 302)