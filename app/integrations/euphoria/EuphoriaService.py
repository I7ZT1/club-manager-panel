import hmac
import json
import hashlib
import requests
from pydantic import BaseModel, HttpUrl, validator, Field, EmailStr, ValidationError
from typing import Union, List
from enum import Enum
#from ipaddress import IPv4Address, IPv6Address
import re


class TypeIDEnum(int, Enum):
    E_COM_H2H = 2
    P2P_H2H = 3
    P2P_PAYMENT_PAGE = 4
    E_COM_PAYMENT_PAGE = 5
    CRYPTO_H2H = 7
    CRYPTO_PAYMENT_PAGE = 8
    QR = 9
    CRYPTO_FIAT_PAYMENT_PAGE = 10


class PayerInfoSchema(BaseModel):
    userAgent: str = Field(..., description="UserAgent от браузера")
    IP: str = Field(..., description="IP клиента")
    userID: str = Field(..., description="IP клиента")
    fingerprint: str = Field(..., description="FingerPring")
    registeredAt: int = Field(..., description="UnixTime")


class ExtraType3(BaseModel):
    methodID: int
    payerInfo: PayerInfoSchema



class InvoiceSchema(BaseModel):
    amount: Union[int, float]
    currencyID: int
    typeID: TypeIDEnum
    clientOrderID: str
    TTL: int
    webhookURL: str
    extra: ExtraType3

    @validator('amount')
    def validate_amount(cls, v, values):
        type_id = values.get('typeID')
        currency_id = values.get('currencyID')
        
        if type_id in {TypeIDEnum.P2P_H2H, TypeIDEnum.P2P_PAYMENT_PAGE}:
            if not isinstance(v, int):
                raise ValueError('Для P2P typeID, amount должен быть целым числом')
        
        if currency_id in {47, 14}:
            if isinstance(v, float) and round(v, 2) != v:
                raise ValueError('Для currencyID 47 и 14, amount должен иметь не более двух десятичных знаков')
        
        return v

    @validator('extra', pre=True)
    def validate_extra(cls, v, values):
        type_id = values.get('typeID')
        if type_id == TypeIDEnum.P2P_H2H:
            # Если v уже является объектом ExtraType3, просто возвращаем его
            if isinstance(v, ExtraType3):
                return v
            # Иначе создаем объект ExtraType3 из словаря
            return ExtraType3(**v)
        return v


class ResponseInvoice(BaseModel):
    status: str
    orderID: int
    accountNumber: str
    accountName: str
    TTL: int
    failCause: str


class EuphoriaService:
    def __init__(self, api_key, secret_key, user_agent, hook_url) -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._user_agent = user_agent
        self._webhook = hook_url
        self.api_url = 'https://api.euphoria.inc'


    def make_signature(self, payload: str = '') -> str:
        return hmac.new(self._secret_key.encode(), payload.encode(), hashlib.sha512).hexdigest()


    def make_headers(self, payload: str) -> dict:
        signature = self.make_signature(payload)
        headers = {
            'Content-Type': "application/json",
            'Signature': signature,
            'User-Agent': self._user_agent,
            'API-Key': self._api_key
        }
        return headers


    def create_order(self, amount: int, any_id: str, second_ttl: int) -> ResponseInvoice:
        info = PayerInfoSchema(userAgent="API CMS", IP="159.148.88.26", userID="010400050905", fingerprint="parampampam", registeredAt=1727372882)
        extra = ExtraType3(methodID=311, payerInfo=info) #  этот ид выдает нам реквизиты
        invoice = InvoiceSchema(
            amount=amount,
            currencyID=7,
            typeID=3,
            clientOrderID=any_id,
            TTL=second_ttl,
            webhookURL=self._webhook,
            extra=extra,
        )
        payload = invoice.model_dump()
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        headers = self.make_headers(payload_str)
        url = f"{self.api_url}/payin/process"
        response = requests.request("POST", url, data=payload_str, headers=headers, timeout=10)

        try:
            return ResponseInvoice(**response.json())
        except:
            return response.json()
        

    def check_order(self, order_id):
        payload={"ID": order_id}
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        headers = self.make_headers(payload_str)
        url = f"{self.api_url}/payin/details"
        response = requests.request("POST", url, data=payload_str, headers=headers, timeout=10)
        return response.json()
    

if __name__ == "__main__":
    api_key = "D8XmxAMW7lOcig1YdfcVvThN8T7Cvo4VAUhSeS0128viOTeW4aQe2dngpRBOTGzTnMhhlCVnxEjsQo4aCB1sOLumbbGIInrXWYiOJX0XVnwOPAALdCUR3EEVM2pWD0mkHb2q2NPzylLUtTdz9W7qEBPrbvPN7kzJNeS03SUERRx4JlqgCcwRU4gxWvsu2wru8cmLSsdvuaUPuLWNLO9ahNKWxHZ7cUR9yETiuEJqVtUtISdrScJ9xNln"
    secret_key = "UMVChf2iSPb3RDtq1rVk9zQWGZaNRVUMD1I8km34SiCYCz1WYQMivCiFAhTLYYXaySHTrbU8o4AGOtOadp2LyDJQryG7T355mMjj45FWedico6gSEk8IwnJ6TWuZOtGfURr4Pz0eGJvguvYxBecRsU1qluSThYE9eb0anrHQRBaYGOke57OmW3ds7oC7QxXBm0soZKi9CYNEGgWfWDyHxgP8WCKMWZxZcViLVx8Z55s9"
    user_agent = '84U{Yk'

    euphoria_service = EuphoriaService(api_key, secret_key, user_agent, "http://cms.clubgg.com.ua/webhook")
    print(euphoria_service.create_order(5000, "1234567890", 3600))