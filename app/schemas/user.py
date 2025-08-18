from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    email: Optional[EmailStr] = None
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_client: Optional[bool] = None
    is_operator: Optional[bool] = None
    is_cashier: Optional[bool] = None

class User(UserBase):
    id: int
    is_admin: bool
    is_client: bool
    is_operator: bool
    is_cashier: bool
    
    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: str