from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, constr, Field
from datetime import datetime


class TransactionDepositData(BaseModel):
    id: int
    fiat_amount: float
    status: str
    curse: float
    time_window: int
    created_at: datetime
    requisities: str
    usdt_amount: float
    owner: str
    bankname: str

    # Переопределение метода для кастомной обработки поля created_at
    @classmethod
    def model_validate(cls, obj):
        if 'created_at' in obj and isinstance(obj['created_at'], str):
            # Преобразование строки в datetime объект
            obj['created_at'] = datetime.strptime(obj['created_at'], '%d.%m.%y, %H:%M')
        return super().model_validate(obj)


class TransactionDeposit(BaseModel):
    status: str
    data: TransactionDepositData



#https://bitconce.top/api/getAccountInfo/
class DepositAccountData(BaseModel):
    balance: str
    balance_fiat: str
    safe_balance: str
    percent: float
    direction: str
    fiat_currency: str
    crypto_currency: str
    notifications: int
    closed_today: int
    sended_fiat_today: str
    withdrawals_today: str


class DepositAccountInfoResponse(BaseModel):
    status: str
    data: DepositAccountData


class WithdrawAccountData(BaseModel):
    balance: float = Field(..., description="Текущий баланс в криптовалюте")
    balance_fiat: int = Field(..., description="Баланс в фиатной валюте")
    safe_balance: float = Field(..., description="Безопасный баланс")
    percent: float = Field(..., description="Процент изменения")
    direction: Literal['sell_btc', 'buy_btc'] = Field(..., description="Направление транзакции")
    fiat_currency: str = Field(..., description="Фиатная валюта")
    crypto_currency: str = Field(..., description="Криптовалюта")
    notifications: int = Field(..., description="Количество уведомлений")
    recieve_today: int = Field(..., description="Получено сегодня")
    closed_today: int = Field(..., description="Закрыто сегодня")
    until_limit: float = Field(..., description="Оставшийся лимит")
    until_limit_fiat: int = Field(..., description="Оставшийся лимит в фиатной валюте")


class WithdrawAccountInfoResponse(WithdrawAccountData):
    status: str
    data: WithdrawAccountData



#/getOrderById/
class DepositOrderData(BaseModel):
    id: str
    fiat_amount: str
    fiat_currency: str
    old_amount: str
    status: str
    time_window: str
    created_at: str
    fromreq: Optional[str] = None
    checked: bool
    ulast_check: Optional[str]
    checked_counter: int
    percent: float
    requisities: str
    sbp_number: Optional[str] = None
    proof1: Optional[str] = None
    proof2: Optional[str] = None
    bankname: str
    owner: str
    last_cancellation_reason: Optional[str] = None
    usdt_amount: str
    curse: float


class DepositOrderResponse(BaseModel):
    status: str
    data: DepositOrderData




class WithdrawAccountData(BaseModel):
    balance: str
    balance_fiat: str
    closed_today: int
    crypto_currency: str
    direction: str  # Если есть конкретный список возможных направлений, можно использовать Literal['sell_btc', '...']
    fiat_currency: str
    notifications: int
    percent: float
    recieve_today: str
    safe_balance: str
    until_limit: int
    until_limit_fiat: str

class WithdrawAccountInfoResponse(BaseModel):
    status: str
    data: WithdrawAccountData



#https://bitconce.top/api/getOrderById/
class OrderDataModel(BaseModel):
    id: str
    bet_id: Optional[str] = None
    fiat_amount: str
    fiat_currency: str
    old_amount: Optional[str] = None
    status: str
    time_window: str
    created_at: str
    fromreq: Optional[str] = None
    checked: bool
    last_check: Optional[str] = None
    checked_counter: int
    notes: str
    percent: float
    requisities: str
    proof1: Optional[str] = None
    proof2: Optional[str] = None
    usdt_amount: str
    curse: float

class GetOrderByIdResponse(BaseModel):
    status: str
    data: OrderDataModel


#https://bitconce.top/api/createOrder/
class OrderRequest(BaseModel):
    fiat_amount: int
    bank_name: Optional[str]
    custom_id: Optional[str]
    sbp: bool
    client_phone: Optional[str]
    exchange_username: Optional[str]
    client_email: Optional[str]
    client_username: Optional[str]


#https://bitconce.top/api/createExOrder/
class OrderWithdrawRequest(BaseModel):
    requisites: int
    rub_amount: int
    custom_id: Optional[str]
    mode: str = 'alone'
    live_time: int = 0
    user_from: int = 3857 #rub # 3864=KZT
    direction: Optional[str] = 'banks'


class OrderDataResponse(BaseModel):
    id: int
    fiat_amount: float
    status: str
    curse: float
    time_window: int
    requisites: str
    usdt_amount: float
    owner: str
    bankname: str
    sbp_number: Optional[str] = None


class OrderResponse(BaseModel):
    status: str
    data: OrderDataResponse


#https://bitconce.top/api/getOrdersList/
class OrderModel(BaseModel):
    id: str
    bet_id: Optional[str] = None
    fiat_amount: str
    fiat_currency: str
    old_amount: Optional[str] = None
    status: str
    time_window: str
    created_at: str
    fromreq: Optional[str] = None
    checked: bool
    last_check: Optional[str] = None
    checked_counter: int
    notes: str
    percent: float
    requisities: str
    proof1: Optional[str] = None
    proof2: Optional[str] = None
    usdt_amount: str
    curse: float

class GetOrdersListResponse(BaseModel):
    status: str
    orders: List[OrderModel]


#https://bitconce.top/api/getOrders/
class OrderModel(BaseModel):
    id: str
    bet_id: Optional[str] = None
    fiat_amount: str
    old_amount: Optional[str] = None
    usdt_amount: str
    status: str
    curse: str
    bonus_percent: int
    time_window: str
    created_at: str
    fromreq: Optional[str] = None
    awaiting_check: bool
    wallet_description: str
    percent: str
    requisities: str

class GetOrdersResponse(BaseModel):
    status: str
    num_pages: int
    count: str
    direction: str
    orders: List[OrderModel]