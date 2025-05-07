# app/services/order_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

from app.models import Order, Trip

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, trip_id: UUID, weight: float, description: str) -> Order:
        order = Order(user_id=user_id, trip_id=trip_id, weight=weight, description=description)
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_for_users(self, customer_id: UUID, carrier_id: UUID) -> Order | None:
        """
        Ищем заказ, где заказчик = customer_id, а trip.user_id = carrier_id.
        """
        stmt = (
            select(Order)
            .join(Trip, Order.trip_id == Trip.id)
            .where(and_(
                Order.user_id == customer_id,
                Trip.user_id  == carrier_id
            ))
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def update_status(self, order: Order, new_status: str):
        order.status = new_status
        await self.db.commit()
        await self.db.refresh(order)
        return order
