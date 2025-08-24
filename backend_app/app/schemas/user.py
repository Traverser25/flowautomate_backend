# app/schemas/user.py
from pydantic import BaseModel, Field
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    name: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class UserPublic(BaseModel):
    id: str
    username: str
    name: Optional[str] = None
    role: str
