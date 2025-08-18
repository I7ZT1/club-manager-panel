from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from core.session import Base
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BitLogsModel(Base):
    __tablename__ = 'BitLogs'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    bank = Column(String, nullable=True)
    spb_rub = Column(Boolean, nullable=True)
    card = Column(String, nullable=True)
    card_details = Column(String, nullable=True)
    currency = Column(String)
    custom_id = Column(Integer, nullable=True)
    user_name = Column(String, nullable=True)
    amount = Column(Float)
    transaction_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), onupdate=func.now())
    bankname = Column(String, nullable=True)
    curse = Column(Float)
    fiat_amount = Column(Float)
    bitconce_id = Column(Integer)
    owner = Column(String)
    requisities = Column(String)
    status = Column(String)
    time_window = Column(Integer)
    usdt_amount = Column(Float)
    sbp = Column(String, nullable=True)


class BitLogSchema(BaseModel):
    type: str
    bank: Optional[str] = None
    spb_rub: Optional[bool] = None
    card: Optional[str] = None
    sbp: Optional[str] = None
    card_details: Optional[str] = None
    currency: str
    custom_id: Optional[int] = None
    user_name: Optional[str] = None
    amount: float
    transaction_id: Optional[int] = None
    created_at: Optional[datetime] = None
    bankname: Optional[str] = None
    curse: float
    fiat_amount: float
    bitconce_id: int
    owner: str
    requisities: str
    status: str
    time_window: int
    usdt_amount: float

    class Config:
        orm_mode = True

class BitLogOutSchema(BitLogSchema):
    id: int



'''
bankname:"Райффайзен Банк RUB"
created_at:"13.02.24, 20:34"
curse:95.97
fiat_amount: "300.0"
id: "48609251"
owner: "Ширина Анастасия Вячеславовна"
requisities: "2200300504316470"
status: "Seller requisite"
time_window: "35"
usdt_amount: "3.125977"
'''


