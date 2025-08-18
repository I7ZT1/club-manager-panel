from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Literal
from datetime import datetime, timezone

class Filters(BaseModel):
    banks: Optional[List[str]] = None
    currencies: Optional[List[str]] = None

    class Config:
        from_attributes = True

class RangeFilter(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None

class BillingCreate(BaseModel):
    billing_name: str
    tax_deposit: Optional[float] = None
    tax_widthdraw: Optional[float] = None
    billing_currency: Optional[str] = None
    card: Optional[str] = None
    card_details: Optional[str] = None
    deposit_limit: Optional[float] = None
    withdraw_limit: Optional[float] = None
    daily_transaction_limit: Optional[int] = None
    monthly_transaction_limit: Optional[int] = None
    clubs: Optional[set[int]] = None
    bank: Optional[str] = None
    soft_delete: bool = False
    min_amount: float = 0
    max_amount: float = 0
    card_balance: float = 0


class Billing(BaseModel):
    id: int
    billing_name: str
    tax_deposit: Optional[float] = None
    tax_widthdraw: Optional[float] = None
    billing_currency: Optional[str] = None
    card: Optional[str] = None
    card_details: Optional[str] = None
    integration_id: Optional[int] = None
    created_at: Optional[datetime] = None
    sort_id: Optional[int] = None
    deposit_limit: Optional[float] = None
    deposit_limit_used: Optional[float] = None
    withdraw_limit: Optional[float] = None
    withdraw_limit_used: Optional[float] = None
    daily_transaction_limit: Optional[int] = None
    daily_transaction_used: Optional[int] = None
    monthly_transaction_limit: Optional[int] = None
    monthly_transaction_used: Optional[int] = None
    attached_clients_count: Optional[int] = None
    soft_delete: bool = False
    min_amount: float = 0
    max_amount: float = 0
    card_balance: float = 0
    clubs: Optional[set[int]] = None
    bank: Optional[str] = None

    class Config:
        from_attributes = True

class BillingFilterFields(BaseModel):
    billing_name: Optional[str] = None
    billing_currency: Optional[str] = None
    soft_delete: Optional[bool] = None
    bank: Optional[str] = None
    card: Optional[str] = None
    created_at: Optional[datetime] = None
    min_amount: Optional[RangeFilter] = None
    max_amount: Optional[RangeFilter] = None
    clubs: Optional[List[int]] = None




class FilterCondition(BaseModel):
    field: str
    op: Literal[
        'eq', 'ne', 'lt', 'lte', 'gt', 'gte', 
        'in', 'not_in', 'like', 'between', 'is_null'
    ]
    value: Any


class BillingAllRequest(BaseModel):
    filters: Optional[List[FilterCondition]] = []
    order_by: Optional[List[str]] = Field(default_factory=list, example=["-created_at"])
    page: int = 1       # Номер страницы для пагинации (необязательный параметр)
    limit: int = 100    # Размер страницы (количество записей)
    class Config:
        from_attributes = True


class BillingResponse(BaseModel):
    data: List[Billing]
    page: int
    tot_pages: int
    total_items: int
    limit: int


