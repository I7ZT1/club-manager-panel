import json
import requests
from typing import Union, Optional
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Literal
from decimal import Decimal
from fastapi import UploadFile, HTTPException


class DepositSchema(BaseModel):
    payment_system: Optional[str] = Field(None, description="Банк kaspi, sber, privat, etc.")
    national_currency: str = Field(description="Валюта банка")
    national_currency_amount: Union[int, float] = Field(description="Сумма для перевода")
    external_order_id: str = Field(description="ID платежа в вашей системе")
    callback_url: str = Field(description="Ссылка на ваш сервер для получения статуса платежа")
    client_merchant_id: str = Field(description="ID клиента в вашей системе")
    trusted_traffic: bool = Field(description="Тип траффика. «true» - первичный трафик (надежный), «false» - вторичный трафик (ненадежный)")
    finger_print: str = Field(description="Уникальный цифровой след устройства пользователя")
    approved_payin_count: Optional[int] = None
    approved_payin_turnover: Optional[Union[int, float]] = None
    approved_payout_count: Optional[int] = None
    approved_payout_turnover: Optional[Union[int, float]] = None



class DepositResponse(BaseModel):
    id: str = Field(description="Уникальный идентификатор платежа для возможного дальнейшего обращения")
    uuid: str = Field(description="Уникальный идентификатор платежа для возможного дальнейшего обращения")
    type: Literal["deposit", "withdrawal"] = Field(description="Тип платежа")
    card_number: str = Field(description="Номер карты в выбранной при запросе платёжной системе или номер счёта")
    expiration_time: str = Field(description="Время, в течении которого необходимо осуществить перевод")
    national_currency: str = Field(description="Валюта для перевода")
    national_currency_amount: str = Field(description="Сумма для перевода")
    payment_system: str = Field(description="Платёжная система для перевода")
    initial_amount: str = Field(description="Изначальная сумма в национальной валюте")
    cryptocurrency_commission_amount: Decimal = Field(description="Общая сумма комиссии, которая будет удержана из суммы платежа в криптовалюте (USDT)")
    national_currency_commission_amount: Decimal = Field(description="Общая сумма комиссии, которая будет удержана из суммы платежа в национальной валюте")
    requisite_type: Literal["card_or_phone_number", "account_number"] = Field(
        description="Тип реквизита (card_or_phone_number - Номер карты/номер телефона, account_number - Номер счёта)"
    )
    
    # Опциональные поля
    expiration_card_date: Optional[str] = Field(None, description="Срок действия карты. Указывается только для BYN валюты")
    payment_link: Optional[str] = Field(None, description="Ссылка платёжной системы для быстрого перевода")
    payment_link_qr_code_url: Optional[str] = Field(None, description="URL адрес SVG изображения QR-кода для быстрого перехода по платёжной ссылке")
    card_owner_name: Optional[str] = Field(None, description="Имя владельца карты в выбранной при запросе платёжной системе")
    sbp_phone_number: Optional[str] = Field(None, description="Номер телефона СБП")
    international_transfer_country: Optional[str] = Field(None, description="Страна международного перевода на латинице")
    international_transfer_country_ru: Optional[str] = Field(None, description="Страна международного перевода на русском")
    trusted_traffic: Optional[bool] = Field(None, description="Тип траффика. «true» - первичный трафик (надежный), «false» - вторичный трафик (ненадежный)")
    approved_payin_count: Optional[int] = Field(None, description="Количество успешных депозитов")
    approved_payin_turnover: Optional[Decimal] = Field(None, description="Сумма успешных депозитов")
    approved_payout_count: Optional[int] = Field(None, description="Количество успешных выводов")
    approved_payout_turnover: Optional[Decimal] = Field(None, description="Сумма успешных выводов")
    finger_print: Optional[str] = Field(None, description="Уникальный цифровой след устройства пользователя")



#Callback Start
class CallbackAttributes(BaseModel):
    uuid: str = Field(description="Универсальный уникальный идентификатор платежа")
    payment_status: Literal["processer_search", "transferring", "confirming", "completed", "cancelled"] = Field(
        description="Статус платежа"
    )
    national_currency_amount: str = Field(description="Сумма для перевода")
    initial_amount: str = Field(description="Изначальная сумма в национальной валюте")
    national_currency: str = Field(description="Валюта для перевода")
    cryptocurrency_commission_amount: Decimal = Field(description="Общая сумма комиссии в криптовалюте (USDT)")
    national_currency_commission_amount: Decimal = Field(description="Общая сумма комиссии в национальной валюте")
    rate: str = Field(description="Курс обмена")
    commission_percentage: str = Field(description="Процент комиссии")
    
    # Опциональные поля
    external_order_id: Optional[str] = Field(None, description="ID платежа в вашей системе")
    cancellation_reason: Optional[Literal[
        "by_client", 
        "duplicate_payment", 
        "fraud_attempt", 
        "incorrect_amount", 
        "not_our_details", 
        "receipt_needed"
    ]] = Field(None, description="Причина отмены платежа")
    arbitration: Optional[bool] = Field(None, description="Флаг арбитража")
    arbitration_reason: Optional[str] = Field(None, description="Причина арбитража")


class CallbackData(BaseModel):
    id: str = Field(description="Идентификатор платежа")
    type: Literal["deposit", "withdrawal"] = Field(description="Тип платежа")
    attributes: CallbackAttributes = Field(description="Атрибуты платежа")


class CallbackPayload(BaseModel):
    data: CallbackData = Field(description="Данные о платеже")
#Callback End


# Сервис для работы с API
class OnePaymentsService:
    def __init__(self, api_key: str, hook_url: str, api_url: Optional[str] = 'https://sandbox.onepayments.tech/api/v1/') -> None:
        self._api_key = api_key
        self._webhook = hook_url #  hook_url
        self.api_url = api_url

    def make_headers(self) -> dict:
        headers = {
            'Content-Type': "application/json",
            'Authorization': self._api_key
        }
        return headers


    def _make_request(self, endpoint, method='GET', headers=None, params=None, json_data=None, data=None, files=None):
        url = f"{self.api_url}{endpoint}"
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
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=json_data, timeout=10)
            print("OnePayment")
            print("--------------------------------")
            print(f"Ответ запроса: {response.status_code}, Text: {response.text}")
            try:
                print(f"Ответ запроса: {response.status_code}, Json: {response.json()}")
            except:
                pass
            print("--------------------------------")
            print(f"payload: {json_data} data: {data}")
            print("--------------------------------")
            print("OnePayment END")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

    def create_order(self, deposit_schema: DepositSchema) -> DepositResponse:
        
        # Поддержка и Pydantic v1, и Pydantic v2
        if hasattr(deposit_schema, 'model_dump'):
            payload = deposit_schema.model_dump()
        else:
            payload = deposit_schema.dict()
        
        #payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        headers = self.make_headers()
        
        # Используем правильный URL из определенных выше констант
        response = requests.request("POST", f"{self.api_url}external_processing/payments/deposits", json=payload, headers=headers, timeout=10)
        #print("OnePayment Error")
        #print("--------------------------------")
        #print(f"Ответ запроса: {response.status_code}, Text: {response.text}")
        #try:
        #    print(f"Ответ запроса: {response.status_code}, Json: {response.json()}")
        #except:
        #    pass
        #print("--------------------------------")
        #print(f"payload: {payload}")
        #print("--------------------------------")
        #print("OnePayment Error END")
        if response.status_code == 422:
            return response.text
        if response.status_code == 200 or response.status_code == 201:
            try:
                # Извлекаем данные из вложенной структуры
                response_data = response.json()
                if 'data' in response_data:
                    data = response_data['data']
                    # Объединяем поля id и type с полями из attributes
                    response_obj = {
                        'id': data.get('id'),
                        'type': data.get('type'),
                        **data.get('attributes', {})
                    }
                    return DepositResponse(**response_obj)
                else:
                    print(f"Ответ не содержит ключ 'data': {response_data}")
                    return response.json()
            except ValidationError as e:
                print(f"Ошибка валидации ответа: {e}")
                return response.json()
        else:
            return response.json()


    def add_receipt(self, uuid: str, document: UploadFile):
        """
        Добавить чек к инвойсу.
        """
        endpoint = f"external_processing/payments/{uuid}/payment_receipts"
        headers = {
                'Authorization': self._api_key,
                'accept': 'application/json'  # Добавляем accept как в curl
            }
        # Подготовка файла для отправки
        files = {
            'image': (document.filename, document.file, document.content_type)
        }
        
        # Подготовка данных формы
        form_data = {
            'start_arbitration': 'false',  # API ожидает строку, а не булево значение
            'comment': '',
            'receipt_reason': ''
        }
        
        # Отправляем запрос без установки Content-Type, так как requests автоматически установит правильный boundary
        return self._make_request(endpoint, method='POST', headers=headers, data=form_data, files=files)


    def change_payment_status(self, payment_id: str, status: str):
        '''
        /api/v1/external_processing/payments/{uuid}/statuses/{event}
        check — проверить переведённые клиентом средства по платёжной системе.
        cancel — отменить платёж.
        '''
        headers = {
            'Authorization': f"{self._api_key}"
        }
        # Поддержка и Pydantic v1, и Pydantic v2
        endpoint = f"external_processing/payments/{payment_id}/statuses/{status}"
        response = self._make_request(f"{endpoint}", method="PATCH", headers=headers)
        return response


# Пример использования
if __name__ == "__main__":
    service = OnePaymentsService(
        api_key="Bearer d37cbaaffa5abab4196cb6b6",
        hook_url="https://your-webhook-url.com",
        api_url="https://sandbox.onepayments.tech/api/v1/"
    )
    data = DepositSchema(
        payment_system=None,#"Kaspi Bank",
        national_currency="KZT",
        national_currency_amount=10000,
        external_order_id="TEST_ORDER_1",
        callback_url="https://cms.clubgg.com.ua/api/webhook/onepayment",
        client_merchant_id="client_456",
        trusted_traffic=True,
        finger_print="unique_fingerprint",
    )
    result_create = service.create_order(data)
    print(result_create)
    #result_change = service.change_payment_status(result_create.uuid, 'cancel')
    #print(result_change)





{
    'payment_system': 'Kaspi Bank', 
    'national_currency': 'KZT', 
    'national_currency_amount': 5000.0, 
    'external_order_id': '139565', 
    'callback_url': 'https://test.klubok-kz.com:7777/api/webhook/onepayment', 
    'client_merchant_id': '1', 
    'trusted_traffic': True, 
    'finger_print': '1', 
    'approved_payin_count': None, 
    'approved_payin_turnover': None, 
    'approved_payout_count': None, 
    'approved_payout_turnover': None
 }

{
    'payment_system': 'Kaspi Bank', 
    'national_currency': 'KZT', 
    'national_currency_amount': 5000.0, 
    'external_order_id': '139566', 
    'callback_url': 'https://test.klubok-kz.com:7777/api/webhook/onepayment', 
    'client_merchant_id': '5839924072', 
    'trusted_traffic': True, 
    'finger_print': '5839924072', 
    'approved_payin_count': None, 
    'approved_payin_turnover': None, 
    'approved_payout_count': None, 
    'approved_payout_turnover': None
 }
