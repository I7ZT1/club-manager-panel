import requests
from pydantic import BaseModel
import hashlib
from fastapi import UploadFile

class PayBridgeDepositSchema(BaseModel):
    amount: float
    order_id: str
    merchant_id: str = ''
    order_desc: str # опис
    currency: str
    version: str



class PayBridgeResponseSchema(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    currency: str
    card: str
    card_owner: str


class PayBridgeErrorSchema(BaseModel):
    status: str
    payment_id: str
    amount: float
    order_id: str
    order_desc: str


class PayBridgeService:
    def __init__(self, api_url: str, merchant_id: str, api_secret: str):
        self._api_url = api_url
        self._merchant_id = merchant_id
        self._api_secret = api_secret

    def _make_request(self, endpoint, method='GET', headers=None, params=None, json_data=None, data=None, files=None) -> dict | None:
        url = f"{self._api_url}{endpoint}"
        if headers is None:
            headers = {}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                if data or files:
                    response = requests.post(url, headers=headers, data=data, files=files, timeout=10)
                else:
                    response = requests.post(url, headers=headers, json=json_data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def create_payment(self, data: PayBridgeDepositSchema) -> PayBridgeResponseSchema:
        path = f"/api/auth/create-payment-api"
        data.merchant_id = self._merchant_id
        # 1. Получаем данные для подписи
        try:
            # Для Pydantic v2+
            params_dict = data.model_dump()
        except AttributeError:
            # Для Pydantic v1
            params_dict = data.dict()
        
        # 2. Сортируем параметры по алфавиту
        sorted_keys = sorted(params_dict.keys())
        
        # 3. Создаем строку параметров в формате "key1|value1|key2|value2|..."
        params_string = '|'.join([f"{key}|{params_dict[key]}" for key in sorted_keys])
        
        # 4. Добавляем секретный ключ
        string_to_sign = f"{params_string}|{self._api_secret}"
        
        # 5. Генерируем SHA-1 хеш
        signature = hashlib.sha1(string_to_sign.encode('utf-8')).hexdigest()
        
        # Добавляем подпись к данным запроса
        request_data = params_dict.copy()
        request_data['amount'] = str(request_data['amount'])
        request_data['signature'] = signature
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = self._make_request(path, method="POST", headers=headers, json_data=request_data)
        try:
            return PayBridgeResponseSchema(**response)
        except Exception as e:
            print({"details": response})
            return {"details": response}
        

    def change_payment_status(self, transaction_id: str):
        """
        Обновляет статус транзакции на "pending"
        
        Args:
            transaction_id (str): Уникальный идентификатор транзакции
            
        Returns:
            dict: Ответ от API
        """
        path = "/api/auth/transaction/update-pending-api"
        
        # Подготовка данных для запроса
        request_data = {
            "merchant_id": self._merchant_id,
            "transactionId": transaction_id
        }
        
        # Создаем строку для подписи (transactionId + merchant_id + "pending")
        string_to_sign = f"merchant_id|{self._merchant_id}|transactionId|{transaction_id}|{self._api_secret}"
        print("STRING: ", string_to_sign)
        # Генерируем SHA-1 хеш
        signature = hashlib.sha1(string_to_sign.encode('utf-8')).hexdigest()
        
        # Добавляем подпись к данным запроса
        request_data['signature'] = signature
        print("SIGNATURE: ", signature)
        headers = {
            "Content-Type": "application/json"
        }
        
        # Отправляем запрос
        response = self._make_request(path, method="POST", headers=headers, json_data=request_data)
        return response


    async def check_payment_uploadfile(self, order_id: int, file: UploadFile):
        path = f"/api/auth/transaction/upload-api"
        data = {
            "merchant_id": self._merchant_id,
            "transactionId": order_id,
        }
        headers = {
            'Accept': 'application/json'
        }
        string_to_sign = f"merchant_id|{self._merchant_id}|transactionId|{order_id}|{self._api_secret}"
        signature = hashlib.sha1(string_to_sign.encode('utf-8')).hexdigest()
        data['signature'] = signature
        files = {'file': (file.filename, file.file, file.content_type)}
        response = self._make_request(path, method="POST", headers=headers, data=data, files=files)
        return response

