from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from datetime import datetime, date


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String)
    birth_date: Mapped[date] = mapped_column(Date) 
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # A user has multiple trips
    trips: Mapped[List["Trip"]] = relationship(back_populates="user")
    # A user has multiple orders
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
    
    # A trip belongs to one user
    user: Mapped["User"] = relationship(back_populates="trips")
    # A trip has multiple orders
    orders: Mapped[List["Order"]] = relationship(back_populates="trip")
        

class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id"))
    
    weight: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # An order belongs to one user
    user: Mapped["User"] = relationship(back_populates="orders")
    # An order belongs to one trip
    trip: Mapped["Trip"] = relationship(back_populates="orders")