from utils.crud import CRUDBase
from components.billing.integration.bitconce.BitSchemas import OrderRequest, OrderResponse, OrderWithdrawRequest
from components.billing.integration.bitconce.BitMS import BitLogsModel, BitLogSchema, BitLogOutSchema
from components.billing.integration.bitconce.BitApiService import BitWithdrawService, BitconceDepService, api_kzt_withdraw_credentials, api_rub_withdraw_credentials, api_kzt_dep_credentials, api_rub_dep_credentials
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from core.session import get_async_db
from fastapi import Depends, HTTPException, status
from components.billing.integration.bitconce.BitMS import BitLogsModel
from sqlalchemy import select

CRUD_bit = CRUDBase[BitLogsModel, BitLogSchema, BitLogSchema]
bitconce_crud = CRUD_bit(BitLogsModel)


bit_dep_rub = BitconceDepService(api_rub_dep_credentials)
bit_dep_kzt = BitconceDepService(api_kzt_dep_credentials)
bit_with_rub = BitWithdrawService(api_rub_withdraw_credentials)
bit_with_kzt = BitWithdrawService(api_kzt_withdraw_credentials)


async def deposit(currency:str, transaction_id:int, order: OrderRequest, session: AsyncSession = Depends(get_async_db)) -> BitLogOutSchema:
    match currency:
        case "RUB":
            bit_order = await bit_dep_rub.createOrder(order)
        case "KZT":
            bit_order = await bit_dep_kzt.createOrder(order)


    data = BitLogSchema(
        type='deposit',
        bank=bit_order.data.bankname,
        spb_rub=order.sbp,
        card=bit_order.data.requisites,
        card_details=bit_order.data.owner,
        currency=currency,
        custom_id=order.custom_id,
        user_name=order.client_username,
        amount=order.fiat_amount,
        transaction_id=transaction_id,
        created_at=datetime.now(),
        bankname=bit_order.data.bankname,
        curse=bit_order.data.curse,
        fiat_amount=bit_order.data.fiat_amount,
        bitconce_id=bit_order.data.id,
        owner=bit_order.data.owner,
        requisities=bit_order.data.requisites,
        status=bit_order.data.status,
        time_window=bit_order.data.time_window,
        usdt_amount=bit_order.data.usdt_amount,
        sbp=bit_order.data.sbp_number
    )

    result = await bitconce_crud.create(session, data)
    return result



async def withdraw(currency:str, transaction_id:int, order: OrderWithdrawRequest, session: AsyncSession = Depends(get_async_db)):
    return True
    match currency:
        case "RUB":
            order.user_from = 3857
            bit_order = await bit_with_rub.createOrder(order)
        case "KZT":
            order.user_from = 3864
            bit_order = await bit_with_kzt.createOrder(order)
        case _:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="No have this currency",
            )


    data = BitLogSchema(
        type='withdraw',
        bank='bitconce',
        spb_rub=None,
        card='bitconce',
        card_details='bitconce',
        currency=currency,
        custom_id=order.custom_id,
        user_name=order.user_from,
        amount=order.rub_amount,
        transaction_id=transaction_id,
        created_at=datetime.now(),
        bankname='bitconce',
        curse='bitconce',
        fiat_amount='bitconce',
        bitconce_id='bitconce',
        owner='bitconce',
        requisities='bitconce',
        status='bitconce',
        time_window='bitconce',
        usdt_amount='bitconce'
    )

    result = await bitconce_crud.create(session, data)
    return result
        



#4400430256700615

    '''
    withdraw
requisites: 5536914064627700
rub_amount: 2000
custom_id: 
mode: alone
live_time: 0
user_from: 3857
direction: banks



    bit_log_example = BitLogOutSchema(
        id=1,
        type="deposit", #dep
        currency="RUB", #currency
        amount=1500.50,
        curse=75.5,
        fiat_amount=113250.0,
        bitconce_id=123456,
        owner="John Doe",
        requisities="Some requisities here",
        status="Pending",
        time_window=30,
        usdt_amount=1500.0,
        created_at=datetime(2024, 2, 15, 12, 0)
    )
    '''

'''

    bit_order_data = {
        "bankname": "Test Bank",
        "curse": 75.5,
        "fiat_amount": 1000.0,
        "id": 123,
        "owner": "John Doe",
        "requisities": "Card Details Example",
        "status": "Pending",
        "time_window": 30,
        "usdt_amount": 1500.0
    }

    order_data = {
        "sbp": True,
        "custom_id": 456,
        "client_username": "client123",
        "fiat_amount": 1000.0
    }

    currency = "USD"
    transaction_id = 789

    # Создание экземпляра BitLogSchema с тестовыми данными
    data = BitLogSchema(
        type='deposit',
        bank=bit_order_data["bankname"],
        spb_rub=order_data["sbp"],
        card=bit_order_data["requisities"],
        card_details=bit_order_data["owner"],
        currency=currency,
        custom_id=order_data["custom_id"],
        user_name=order_data["client_username"],
        amount=order_data["fiat_amount"],
        transaction_id=transaction_id,
        created_at=datetime.now(),
        bankname=bit_order_data["bankname"],
        curse=bit_order_data["curse"],
        fiat_amount=bit_order_data["fiat_amount"],
        bitconce_id=bit_order_data["id"],
        owner=bit_order_data["owner"],
        requisities=bit_order_data["requisities"],
        status=bit_order_data["status"],
        time_window=bit_order_data["time_window"],
        usdt_amount=bit_order_data["usdt_amount"]
    )
'''