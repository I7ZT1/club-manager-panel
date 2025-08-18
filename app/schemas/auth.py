from pydantic import BaseModel, EmailStr
from typing import Optional

# Базовые схемы пользователя
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(BaseModel):
    email: EmailStr
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
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# Схемы аутентификации
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

class UserLogin(BaseModel):
    username: str
    password: str

class RefreshToken(BaseModel):
    refresh_token: str