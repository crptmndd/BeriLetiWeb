from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from datetime import datetime


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String)
    birth_date: Mapped[datetime] = mapped_column(DateTime)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    user: Mapped["Trip"] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    
    
class Trip(Base): 
    __tablename__ = "trips"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    
    from_location: Mapped[str] = mapped_column(String)
    to_location: Mapped[str] = mapped_column(String)
    departure_date: Mapped[datetime] = mapped_column(DateTime)
    max_weight: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    user: Mapped["User"] = relationship(back_populates="trips")
    orders: Mapped["Order"] = relationship(back_populates="trips")
        

class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id"))
    
    weight: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    user: Mapped["User"] = relationship(back_populates="orders")
    trip: Mapped["Trip"] = relationship(back_populates="orders")