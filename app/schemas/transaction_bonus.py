from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime

class StatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class TransactionBonus(BaseModel):
    id: Optional[int] = None
    transaction_id: int
    bonus_id: int
    ticket_value: Optional[float] = None
    chips: Optional[float] = None
    status: StatusEnum = StatusEnum.PENDING
    data: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = Field(default_factory=datetime.now)
    is_send: Optional[bool] = False

    class Config:
        model_validate = True