from datetime import datetime, timedelta
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import settings
from core.db import get_session
from models.UserModel import UserModel

# Настройка для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2 с endpoint для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Функция для верификации пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Функция для хеширования пароля
def get_password_hash(password):
    return pwd_context.hash(password)

# Функция для поиска пользователя по имени пользователя
async def get_user_by_username(session: AsyncSession, username: str):
    result = await session.execute(
        select(UserModel).where(UserModel.username == username)
    )
    return result.scalars().first()

# Функция для поиска пользователя по email
async def get_user_by_email(session: AsyncSession, email: str):
    result = await session.execute(
        select(UserModel).where(UserModel.email == email)
    )
    return result.scalars().first()

# Функция аутентификации пользователя
async def authenticate_user(session: AsyncSession, username: str, password: str):
    # Сначала пробуем найти по username
    user = await get_user_by_username(session, username)
    
    # Если не нашли, пробуем по email
    if not user:
        user = await get_user_by_email(session, username)
    
    # Если всё ещё не нашли или пароль неверный
    if not user or not verify_password(password, user.hashed_password):
        return False
        
    return user

# Создание JWT токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Проверка текущего пользователя
async def get_current_user(session: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(session, username=username)
    if user is None:
        raise credentials_exception
    return user

# Проверка прав администратора
async def get_admin_user(current_user: UserModel = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Insufficient permissions"
        )
    return current_user

# Проверка прав оператора
async def get_operator_user(current_user: UserModel = Depends(get_current_user)):
    if not current_user.is_operator and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Insufficient permissions"
        )
    return current_user

# Проверка прав кассира
async def get_cashier_user(current_user: UserModel = Depends(get_current_user)):
    if not current_user.is_cashier and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Insufficient permissions"
        )
    return current_user

# Проверка прав клиента
async def get_client_user(current_user: UserModel = Depends(get_current_user)):
    if not current_user.is_client and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Insufficient permissions"
        )
    return current_user

# Обновление токена доступа для пользователя
async def update_user_token(session: AsyncSession, user: UserModel, token: str):
    user.access_token = token
    user.token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

# Создание токена обновления
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt