from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.auth import get_session
from models.BIllingModel import BillingModel
from utils.crud import CRUDBase
from schemas.Billing import Filters, Billing, BillingCreate, BillingAllRequest, BillingResponse
from typing import Optional
import json
from typing import Any
from typing import List
from sqlalchemy import select, func

router = APIRouter(prefix="/billing", tags=["billing"])


CRUD = CRUDBase[BillingModel, Billing, Billing]
crud_service = CRUD(BillingModel)




router = APIRouter(prefix="/billing", tags=["billing"])

CRUD = CRUDBase[BillingModel, Billing, Billing]
crud_service = CRUD(BillingModel)

@router.get("/filters", response_model=Filters)
async def get_filters(session: AsyncSession = Depends(get_session)):
    '''Возвращает список валют и банков'''
    sql = select(BillingModel.bank, BillingModel.billing_currency).distinct()
    result = await session.execute(sql)
    billing = result.all()
    # Фильтруем None значения и получаем уникальные значения через set
    banks = list(set([row[0] for row in billing if row[0] is not None]))
    currencies = list(set([row[1] for row in billing if row[1] is not None]))
    return Filters(banks=banks, currencies=currencies)


@router.post("/create")
async def create_billing(billing: BillingCreate, session: AsyncSession = Depends(get_session)):
    return await crud_service.create(session, billing)

@router.post("/all", response_model=BillingResponse)
async def get_all_billings(
    data: BillingAllRequest,
    db: AsyncSession = Depends(get_session)
) -> Any:
    offset = (data.page - 1) * data.limit

    query = select(func.count()).select_from(BillingModel)
    query = crud_service.apply_filters(query, data.filters)
    result = await db.execute(query)
    total_count = result.scalar_one()

    # Получаем записи, передавая order_by напрямую
    result = await crud_service.get_multi(
        db,
        filter_list=data.filters,
        offset=offset,
        limit=data.limit,
        order_by=data.order_by  # Передаем order_by напрямую
    )

    total_pages = (total_count + data.limit - 1) // data.limit

    return BillingResponse(
        data=result,
        page=data.page,
        tot_pages=total_pages,
        total_items=total_count,
        limit=data.limit
    )



@router.get("/{billing_id}")
async def get_billing(billing_id: int, session: AsyncSession = Depends(get_session)):
    return await crud_service.get(session, billing_id)

@router.put("/{billing_id}")
async def update_billing(billing_id: int, billing: BillingCreate, session: AsyncSession = Depends(get_session)):
    return await crud_service.update(session, obj_id=billing_id, obj_in=billing)

@router.delete("/{billing_id}")
async def delete_billing(billing_id: int, session: AsyncSession = Depends(get_session)):
    '''Ставит флаг soft_delete в True'''
    sql = select(BillingModel).where(BillingModel.id == billing_id)
    result = await session.execute(sql)
    billing = result.scalar_one_or_none()
    if billing is None:
        raise HTTPException(status_code=404, detail="Billing not found")
    billing.soft_delete = True
    session.add(billing)
    await session.commit()
    return billing