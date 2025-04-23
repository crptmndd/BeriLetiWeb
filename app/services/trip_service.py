from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Trip
from app.schemas import TripCreate
from uuid import UUID
from typing import Optional
from datetime import date


class TripService: 
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_trip_by_id(self, trip_id: UUID):
        result = await self.db.execute(select(Trip).filter(Trip.id == trip_id))
        return result.scalar_one_or_none()
    
    async def get_all_trips(self):
        result = await self.db.execute(select(Trip))
        return result.scalars().all()
    
    async def create_trip(self, trip_data: TripCreate):
        new_trip = Trip(
            from_location=trip_data.from_location,
            to_location=trip_data.to_location,
            departure_date=trip_data.departure_date,
            max_weight=trip_data.max_weight,
            price=trip_data.price,
            comment=trip_data.comment
        )
        
        self.db.add(new_trip)
        await self.db.commit()
        await self.db.refresh(new_trip)
        return new_trip
    
    async def search_trips(self, from_location: Optional[str] = None, to_location: Optional[str] = None, departure_date: Optional[date] = None):
        query = select(Trip)
        if from_location:
            query = query.filter(Trip.from_location.ilike(f"%{from_location}%"))
        if to_location:
            query = query.filter(Trip.to_location.ilike(f"%{to_location}%"))
        if departure_date:
            query = query.filter(Trip.departure_date == departure_date)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_trip(self, trip: Trip):
        await self.db.delete(trip)
        await self.db.commit()