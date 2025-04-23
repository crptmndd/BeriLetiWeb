from pydantic import BaseModel
from datetime import date
from typing import Optional
from datetime import date
from uuid import UUID


class UserCreate(BaseModel):
    phone_number: str
    full_name: str
    birth_date: date
    password: str
    

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    
    
class TripCreate(BaseModel):
    from_location: str
    to_location: str
    departure_date: date
    max_weight: float
    price: float
    comment: Optional[str] = None
    
class OrderQuery(BaseModel):
    from_location: str
    to_loation: str
    weight: float
    