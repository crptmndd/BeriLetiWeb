from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String)
    birth_date: Mapped[date] = mapped_column(Date)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    trips: Mapped[List["Trip"]] = relationship(back_populates="user")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", 
        foreign_keys="Message.sender_id",
        back_populates="sender"
    )
    received_messages: Mapped[List["Message"]] = relationship(
        "Message", 
        foreign_keys="Message.receiver_id",
        back_populates="receiver"
    )
    
    
class Trip(Base): 
    __tablename__ = "trips"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
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
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trips.id"))
    
    weight: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # An order belongs to one user
    user: Mapped["User"] = relationship(back_populates="orders")
    # An order belongs to one trip
    trip: Mapped["Trip"] = relationship(back_populates="orders")
    
    
class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    receiver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    sender: Mapped["User"] = relationship(
        "User", 
        foreign_keys="Message.sender_id",
        back_populates="sent_messages"
    )
    receiver: Mapped["User"] = relationship(
        "User", 
        foreign_keys="Message.receiver_id",
        back_populates="received_messages"
    )
    
    
    
class Reviews(Base):
    __tablename__ = "reviews"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    rating: Mapped[float] = mapped_column(Float)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewer_id])
    reviewee: Mapped["User"] = relationship("User", foreign_keys=[reviewee_id])