from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from core.db import get_session
from dependencies.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_password_hash, get_user_by_email, get_user_by_username, update_user_token
)
from core.config import settings
from models.UserModel import UserModel
from schemas.auth import Token, TokenPayload, UserCreate, UserLogin, RefreshToken

router = APIRouter(prefix="/auth", tags=["Аутентификация"])

@router.post("/register", response_model=Token)
async def register_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    # Проверка существования пользователя
    db_user = await get_user_by_email(session, email=user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    # Создание нового пользователя
    hashed_password = get_password_hash(user_data.password)
    db_user = UserModel(
        username=user_data.email,
        email=user_data.email,
        hashed_password=hashed_password,
        is_client=True  # По умолчанию создаем клиента
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    # Создание токенов
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": db_user.username})
    
    # Обновление токена в базе
    await update_user_token(session, db_user, access_token)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # Обновление токена в базе
    await update_user_token(session, user, access_token)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login_for_access_token_json(
    user_data: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(session, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # Обновление токена в базе
    await update_user_token(session, user, access_token)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshToken,
    session: AsyncSession = Depends(get_session)
):
    try:
        payload = jwt.decode(
            token_data.refresh_token, 
            settings.REFRESH_SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен обновления"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен обновления"
        )
        
    user = await get_user_by_username(session, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Обновление токена в базе
    await update_user_token(session, user, access_token)
    
    return {"access_token": access_token, "refresh_token": token_data.refresh_token, "token_type": "bearer"}