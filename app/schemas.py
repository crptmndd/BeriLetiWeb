from pydantic import BaseModel
from datetime import date
from typing import Optional


class UserCreate(BaseModel):
    phone_number: str
    full_name: str
    birth_date: date
    password: str
    

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None