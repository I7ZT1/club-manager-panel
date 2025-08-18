from core.db import Base
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean(), default=False)
    is_client = Column(Boolean(), default=False)
    is_operator = Column(Boolean, default=False)
    is_cashier = Column(Boolean, default=False)

    # Токены для аутентификации/восстановления пароля
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    password_reset_token = Column(String, nullable=True)
    
    # Срок действия токенов
    token_expires = Column(DateTime, nullable=True)
    
    # Полезно добавить временные метки
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
