from fastapi import APIRouter, Depends, Response
from utils.crud import CRUDBase
from models.TransactionBonusModel import TransactionBonusModel
from schemas.transaction_bonus import TransactionBonus
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_session
from typing import Optional

router = APIRouter(prefix="/client-bonus", tags=["Бонусы"])

CRUDTransfer = CRUDBase[TransactionBonusModel, TransactionBonus, TransactionBonus]
crud_transfer = CRUDTransfer(TransactionBonusModel)


@router.get("/all")
async def get_client_bonus(
        page: int = 1,
        limit: int = 100,
        is_receipt: Optional[bool] = None,
        db: AsyncSession = Depends(get_session)
    ):
    stmt = select(TransactionBonusModel)
    if is_receipt is not None:
        stmt = stmt.where(TransactionBonusModel.is_receipt == is_receipt)
    stmt = stmt.order_by(TransactionBonusModel.created_at.desc())
    stmt = stmt.offset((page - 1) * limit).limit(limit) # 127, 128, 129, 130
    result = await db.execute(stmt)
    receipts = result.scalars().all()

    # Пагинация и сортировка нужно получить количество записе (total_items) и высчитать количество страниц (tot_pages)
    stmt_count = select(TransactionBonusModel)
    count = select(func.count()).select_from(stmt_count)
    count_rows = await db.execute(count)
    total_items = count_rows.scalar_one()
    tot_pages = (total_items + limit - 1) // limit

    return {
        "data": [TransactionBonus.model_validate(receipt.__dict__) for receipt in receipts],
        "page": page,
        "tot_pages": tot_pages,
        "total_items": total_items,
        "limit": limit
    }


@router.patch("/{bonus_id}/send")
async def mark_bonus_as_sent(
    bonus_id: int,
    db: AsyncSession = Depends(get_session)
):
    stmt = select(TransactionBonusModel).where(TransactionBonusModel.id == bonus_id)
    result = await db.execute(stmt)
    bonus = result.scalar_one_or_none()
    
    if not bonus:
        return Response(status_code=404)
    
    if bonus.is_send:
        bonus.is_send = False
    else:
        bonus.is_send = True
    await db.commit()
    
    return bonus

