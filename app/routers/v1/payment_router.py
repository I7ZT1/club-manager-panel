from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from core.db import get_session
from models.BIllingModel import BillingModel

router = APIRouter(prefix="/payment", tags=["Платежи"])

class PaymentRequest(BaseModel):
    rating: int  # рейтинг влияет на выбор карты. К примеру первые депозиты идут на карту помеченную как risk
    amount: float # сумма депозита
    currency: str # валюта депозита
    settlement: bool # Указывает можно ли использовать внутреннюю платежную систему под названием settlement
    club_id: int # id клуба
    cards: bool # Указывает на то что если есть лимиты на карты, то сначала использовать их
    crypto: bool # Указывает использовать криптовалюту
    bank: str #  Добавляет фильтр по банку
    billing_id: int # Использует определенную карту из биллинга или платежного провайдера

class PaymentRequisites(BaseModel):
    client_id: int # id клиента
    card_number: str # номер карты
    card_details: str # детали карты
    bank: str # банк
    amount: float # сумма
    currency: str # валюта
    billing_id: int # id биллинга
    billing_status: str # статус биллинга исторично сложилось что может быть UUID
    billing_usd: float # сумма в долларах
    currency_rate: float # курс валюты


@router.post("/requisites", response_model=PaymentRequisites)
async def get_payment_requisites(
    payment_data: PaymentRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Получение реквизитов для оплаты
    Отправляется сумма и валюта, возвращаются реквизиты карты
    """
    # Логика выбора подходящей карты
    query = select(BillingModel).where(
        BillingModel.billing_currency == payment_data.currency,
        BillingModel.soft_delete == False,
        BillingModel.min_amount <= payment_data.amount,
        BillingModel.max_amount >= payment_data.amount
    ).order_by(BillingModel.sort_id)
    
    result = await session.execute(query)
    billing = result.scalar_one_or_none()
    
    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Нет доступных реквизитов для валюты {payment_data.currency} и суммы {payment_data.amount}"
        )
    
    return PaymentRequisites(
        card_number=billing.card,
        card_details=billing.card_details,
        bank=billing.bank,
        amount=payment_data.amount,
        currency=payment_data.currency,
        billing_id=billing.id
    )
