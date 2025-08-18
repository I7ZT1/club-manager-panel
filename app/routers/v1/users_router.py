from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from core.db import get_session
from dependencies.auth import get_admin_user, get_current_user, get_password_hash
from models.UserModel import UserModel
from schemas.user import User, UserUpdate, UserCreate, UserInDB

router = APIRouter(prefix="/users", tags=["Пользователи"])

@router.get("/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_data: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Обновление данных текущего пользователя
    if user_data.username is not None:
        current_user.username = user_data.username
    if user_data.email is not None:
        current_user.email = user_data.email
    if user_data.password is not None:
        current_user.hashed_password = get_password_hash(user_data.password)
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: UserModel = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(UserModel).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users

@router.post("/", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    # Проверка существования пользователя
    result = await session.execute(
        select(UserModel).where(UserModel.email == user_data.email)
    )
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    # Создание нового пользователя
    hashed_password = get_password_hash(user_data.password)
    db_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin,
        is_client=user_data.is_client,
        is_operator=user_data.is_operator,
        is_cashier=user_data.is_cashier
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    current_user: UserModel = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return db_user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserModel = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Обновление данных пользователя
    if user_data.username is not None:
        db_user.username = user_data.username
    if user_data.email is not None:
        db_user.email = user_data.email
    if user_data.password is not None:
        db_user.hashed_password = get_password_hash(user_data.password)
    if user_data.is_admin is not None:
        db_user.is_admin = user_data.is_admin
    if user_data.is_client is not None:
        db_user.is_client = user_data.is_client
    if user_data.is_operator is not None:
        db_user.is_operator = user_data.is_operator
    if user_data.is_cashier is not None:
        db_user.is_cashier = user_data.is_cashier
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    await session.delete(db_user)
    await session.commit()
    return {"status": "success"}