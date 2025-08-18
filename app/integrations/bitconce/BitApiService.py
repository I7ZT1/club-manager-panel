from components.billing.integration.bitconce.BitSchemas import OrderResponse, DepositAccountInfoResponse, WithdrawAccountInfoResponse, OrderWithdrawRequest, OrderRequest, DepositOrderResponse
from utils.APIClient import APIClient
from core.config import settings
from fastapi import HTTPException, status
from core.session import get_async_db
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from components.billing.integration.bitconce.BitMS import BitLogsModel
from typing import Optional

async def get_order_id(custom_id: int) -> Optional[int]:
    async for db in get_async_db():
        async with db.begin():
            stmt = select(BitLogsModel).where(BitLogsModel.custom_id == custom_id)
            result = await db.execute(stmt)
            bit_log_model = result.scalars().first()
            if not bit_log_model:
                return None
            return bit_log_model.bitconce_id


api_rub_dep_credentials = APIClient(
    base_url="https://bitconce.top/api", 
    headers={'Authorization': f'Bearer {settings.deposit_rub}'}
)

api_kzt_dep_credentials = APIClient(
    base_url="https://bitconce.top/api",
    headers={'Authorization': f'Bearer {settings.deposit_kzt}'}
)

api_rub_withdraw_credentials = APIClient(
    base_url="https://bitconce.top/api",
    headers={'Authorization': f'Bearer {settings.withdraw_rub}'}
)

api_kzt_withdraw_credentials = APIClient(
    base_url="https://bitconce.top/api",
    headers={'Authorization': f'Bearer {settings.withdraw_kzt}'}
)

class BitconceDepService:
    def __init__(self, api: APIClient) -> None:
        self.api = api

    async def getAccountInfo(self) -> DepositAccountInfoResponse:
        account_info = await self.api.get("/getAccountInfo/")
        result = DepositAccountInfoResponse(**account_info)
        return result
        

    async def getOrderById(self, order_id: int) -> DepositOrderResponse:
        params = {'order_id': order_id}
        data = await self.api.get(path="/getOrderById/", params=params)
        result = DepositOrderResponse(**data)
        return result


    async def createOrder(self, create: OrderRequest) -> OrderResponse:
        print(f"BitConce Create: order request {create}")

        data = await self.api.post("/createOrder/", form_data=create.model_dump())
        print(f"BitConce send response: {data}")

        if not data:
            from components.billing.services.TransactionServices import transaction_crud
            async for db in get_async_db():
                async with db.begin():
                    await transaction_crud.edit_values_by_id(db, int(create.custom_id), {'transaction_status_id': 7})
            
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="BitConce don't send response...",
            )
        
        if data['status'] != "success":
            from components.billing.services.TransactionServices import transaction_crud
            async for db in get_async_db():
                async with db.begin():
                    await transaction_crud.edit_values_by_id(db, int(create.custom_id), {'transaction_status_id': 7})
            
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=data['description'],
            )
        order_info = OrderResponse(**data)
        return order_info


    async def change_order_data(self, custom_id: str, proof: UploadFile = None, fiat_amount: float = None, files=None):
        order_id = await get_order_id(int(custom_id))

        if not order_id:
            raise f"Order ID: {order_id}"

        print(f"BitConce Change Order Data: order_id {order_id}, custom_id {custom_id}, fiat_amount {fiat_amount}")
        
        # Подготовка данных формы
        form_data = {
            'order_id': order_id,
            'fiat_amount': str(fiat_amount) if fiat_amount is not None else '',
            'message': ''
        }
        # Подготовка файлов
        files = {}

        # Обработка первого файла 'proof'
        if proof is not None:
            proof_content = await proof.read()
            files['proof'] = (proof.filename, proof_content, proof.content_type)
        else:
            # Если файла нет, отправляем пустой файл с соответствующим MIME-типом
            files['proof'] = ('', b'')

        files['proof_2'] = ('', b'')


        data = await self.api.send_files("/checkOrder/", data=form_data, files=files)
        print(f"BitConce change order response: {data}")

        # Проверка успешности ответа
        if not data or data.get('status') != "success":
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=data.get('description', "BitConce don't send response..."),
            )

        # Преобразование данных ответа в нужный формат
        order_info = OrderResponse(**data)
        return order_info




'''
test_data = OrderRequest(
    fiat_amount= 333,
    bank_name="all",
    custom_id=None,
    sbp=False,
    exchange_username="Client X",
    client_username="VICTOR",
    client_email=None,
    client_phone=None
)

res = asyncio.run(BitconceDepService(api_rub_dep).createOrder(test_data))
print(res)

'''


class BitWithdrawService:
    def __init__(self, api: APIClient) -> None:
        self.api = api

    async def getAccountInfo(self) -> WithdrawAccountInfoResponse:
        account_info = await self.api.get("/getAccountInfo/")
        result = WithdrawAccountInfoResponse(**account_info)
        return result
    

    async def createOrder(self, create: OrderWithdrawRequest) -> OrderResponse:
        data = await self.api.post("/createExOrder/", form_data=create.model_dump())
        if data['status'] != "success":
            print(data)
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=data['description'],
            )
        return True




'''
data = OrderWithdrawRequest(
    requisites=4400430256700615,rub_amount=20000,custom_id='1',mode='alone',live_time=0,user_from=3864,direction='banks'
)

res = asyncio.run(WithdrawKZT(api_kzt_withdraw_credentials).createOrder(data))
print(res)
'''
