import hmac
import hashlib
import requests
import json
from pydantic import BaseModel
from typing import Optional
from pprint import pprint

class ResponseCreate(BaseModel):
    success: bool
    id: int
    bill_id: str
    amount: float
    card_number: str
    bank: str
    name: str


class ResponseInfo(BaseModel):
    id: int
    client_order_id: str
    created: str
    updated: str
    bill_id: str
    fee: float
    order_type: str
    comment: Optional[str]
    status: str
    amount: float
    currency: str


class PlatiPaysService:
    BASE_URL = "https://partner-api.chatlpays.com"

    def __init__(self, callback_url: str, APIKEY: str, secret_key: str):
        self._APIKEY = APIKEY
        self._SECRET_KEY = secret_key
        self.callback_url = callback_url

    def make_signature(self, payload: str = '') -> str:
        return hmac.new(self._SECRET_KEY.encode(), payload.encode(), hashlib.sha512).hexdigest()

    def make_headers(self, payload: str) -> dict:
        payload_str = json.dumps(payload)  # возможно вернут separators=(',', ':')
        signature = self.make_signature(payload_str)
        pprint(signature)
        headers = {
            'Content-Type': "application/json",
            'Signature': signature,
            'APIKEY': self._APIKEY
        }
        return headers

    def create_order(self, amount: float, order_id: str, user_id: str) -> ResponseCreate:
        url = f"{self.BASE_URL}/payment/deposit"

        payload = {
            "client_order_id": str(order_id),
            "user_id": str(user_id),
            "amount": amount,
            "comment": "Top-up",
            "expire": 1200,
            "user_ip": "95.164.91.240",
            "currency_id": 1,
            "callback": f"{self.callback_url}/{order_id}",
        }

        headers = self.make_headers(payload)
        pprint(payload)
        resp = requests.post(url, headers=headers, json=payload)
        
        response_data = resp.json()
        print(response_data)
        return ResponseCreate(**response_data)


    def details_order(self, bill_id: str, order_type: str) -> ResponseInfo:
        url = f"{self.BASE_URL}/payment/details"

        payload = {
            "bill_id": bill_id,
            "order_type": order_type
        }

        headers = self.make_headers(payload)
        pprint(payload)
        resp = requests.post(url, headers=headers, json=payload)
        
        response_data = resp.json()
        pprint(response_data)
        print("")
        return ResponseInfo(**response_data)



'''
service = PlatiPaysService(
    callback_url='https://partner-api.chatlpays.com',
    APIKEY='1',
    secret_key='2'
)
print(service.details_order('216b7f45-f3f8-4319-a658-0e8d6abc3d55', 'deposit'))
#data = service.create_order(400, 'req7188823', 'user463964')
#print(data)
'''