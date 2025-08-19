from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ARRAY
from sqlalchemy.sql import func
from core.db import Base

class BillingModel(Base):
    __tablename__ = 'billings'
    id = Column(Integer, primary_key=True, index=True)
    billing_name = Column(String)
    tax_deposit = Column(Float, nullable=True)
    tax_widthdraw = Column(Float, nullable=True)
    billing_currency = Column(String, nullable=True)
    card = Column(String, nullable=True)
    card_details = Column(String, nullable=True)
    integration_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), onupdate=func.now())
    sort_id = Column(Integer, nullable=True)
    deposit_limit = Column(Float, nullable=True) #n
    deposit_limit_used = Column(Float, nullable=True) #n
    withdraw_limit = Column(Float, nullable=True) #n
    withdraw_limit_used = Column(Float, nullable=True) #n
    daily_transaction_limit = Column(Integer, nullable=True) # Количество лимит транзакций в день
    daily_transaction_used = Column(Integer, nullable=True) # Количество использованных транзакций в день
    monthly_transaction_limit = Column(Integer, nullable=True) # Количество транзакций в месяц
    monthly_transaction_used = Column(Integer, nullable=True) # Количество использованных транзакций в месяц
    attached_clients_count = Column(Integer, nullable=True)
    soft_delete = Column(Boolean, default=False)
    min_amount = Column(Float, default=0)
    max_amount = Column(Float, default=0)
    card_balance = Column(Float, default=0)
    clubs = Column(ARRAY(Integer), nullable=True)
    bank = Column(String, nullable=True)
    risk = Column(Boolean, default=False) # TODO: Добавить поле в бд для отметки карты как рисковая