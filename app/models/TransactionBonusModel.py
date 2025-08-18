from sqlalchemy import Column, Integer, Enum as SAEnum, DateTime, String, Float, Boolean
from core.db import Base
from sqlalchemy.sql import func
from enum import Enum

class StatusEnum(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class TransactionBonusModel(Base):
    __tablename__ = 'transaction_bonuses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, nullable=False)
    bonus_id = Column(Integer, nullable=False)
    ticket_value = Column(Float, nullable=True)
    chips = Column(Float, nullable=True)

    # Указываем имя ENUM для PostgreSQL
    status = Column(SAEnum(StatusEnum, name="status_enum"), nullable=False, default=StatusEnum.PENDING)
    
    data = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), server_onupdate=func.now())
    scheduled_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=True)  # Добавленное поле для даты начисления
    is_send = Column(Boolean, nullable=True, default=False)

    def __repr__(self):
        return f"<BonusTransaction(id={self.id}, transaction_id={self.transaction_id}, bonus_id={self.bonus_id}, status='{self.status}')>"