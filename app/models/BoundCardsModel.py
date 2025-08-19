from sqlalchemy import Column, Integer, DateTime, Boolean, BigInteger
from sqlalchemy.sql import func
from core.session import Base

class BoundCardsModel(Base):
    __tablename__ = 'bound_cards'
    id = Column(Integer, primary_key=True, index=True)
    amo_id = Column(BigInteger, nullable=False)
    billing_id = Column(Integer, nullable=False)
    used_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    active = Column(Boolean, default=True)