# app/services/chat_service.py
from typing import List, Dict
from uuid import UUID
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.services.user_service import UserService

from app.models import Message

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_conversations(self, user_id: UUID) -> List[Dict]:
        """
        Возвращает список уникальных peer_id, с которыми общался user_id,
        и информацию по каждому собеседнику.
        """
        stmt = select(Message.sender_id, Message.receiver_id).where(
            or_(Message.sender_id == user_id, Message.receiver_id == user_id)
        )
        res = await self.db.execute(stmt)
        pairs = res.all()

        peer_ids = set()
        for s, r in pairs:
            if s != user_id: peer_ids.add(s)
            if r != user_id: peer_ids.add(r)

        result = []
        user_svc = UserService(self.db)
        for pid in peer_ids:
            u = await user_svc.get_user_by_id(pid)
            if u:
                result.append({
                    "id": str(u.id),
                    "full_name": u.full_name,
                    "avatar": u.avatar,
                    "rating": u.rating
                })
        return result

    async def get_history(self, user_id: UUID, peer_id: UUID) -> List[Dict]:
        """
        Возвращает список сообщений между user_id и peer_id
        """
        stmt = select(Message).where(
            or_(
                and_(Message.sender_id == user_id,    Message.receiver_id == peer_id),
                and_(Message.sender_id == peer_id,   Message.receiver_id == user_id),
            )
        ).order_by(Message.created_at)
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        return [self._serialize(m) for m in messages]

    async def save_message(self, sender_id: UUID, receiver_id: UUID, content: str) -> Dict:
        """
        Сохраняет новое сообщение и возвращает его в сериализованном виде
        """
        msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            created_at=datetime.utcnow()
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return self._serialize(msg)

    def _serialize(self, msg: Message) -> Dict:
        return {
            "sender_id": str(msg.sender_id),
            "receiver_id": str(msg.receiver_id),
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }
