import requests
from pydantic import BaseModel
from typing import Tuple
from fastapi import UploadFile

class SharkPayData(BaseModel):
    paydeskId: int
    way: str
    orderId: str
    clientEmail: str
    price: float
    url: str
    currencyCode: str

class SharkPaySignatureRequest(BaseModel):
    data: SharkPayData

class SharkPaySignatureResponse(BaseModel):
    signature: str

class PaymentOffer(BaseModel):
    id: int
    cardNumber: str
    holderName: str
    image: str
    bankName: str

class PaymentOffersResponse(BaseModel):
    paymentOffer: PaymentOffer
    paymentId: int
    timeLimit: int

class SharkPayService:
    def __init__(self, token: str, api_url: str = "https://bc.sharkpay.team", url_cashier: str = 'https://test.klubok-kz.com'):
        self._api_url = api_url
        self.token = token
        self.url = url_cashier


    def _make_request(self, endpoint: str, method='POST', headers=None, json_data=None, files=None):
        url = f"{self._api_url}{endpoint}"
        if headers is None:
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
        print("KlubOK send headers:", headers)
        print("KlubOK send payload:", json_data)
        try:
            response = requests.request(method, url, headers=headers, json=json_data, files=files, timeout=10)
            #response.raise_for_status()


            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                print("ShakPay send:")
                print(response.json())
                return response.json()
            else:
                return response.content
        except requests.exceptions.HTTPError as e:
            print(f"SharkPayService Request error: {e}")
            if e.response is not None:
                print("SharkPayService Server response:", e.response.text)
                return response
            return None
        except requests.exceptions.RequestException as e:
            print(f"SharkPayService Request error: {e}")
            return None

    def generate_signature(self, paydesk_id: int, way: str, order_id: str, client_email: str, price: float, currencyCode: str, url:str = None) -> SharkPaySignatureResponse:
        endpoint = "/api/payments/signature/generate"
        if not url:
            url = self.url
        request_data = SharkPaySignatureRequest(
            data=SharkPayData(
                paydeskId=paydesk_id,
                way=way,
                orderId=order_id,
                clientEmail=client_email,
                price=price,
                currencyCode=currencyCode,
                url=url
            )
        )

        # Используем model_dump вместо dict для совместимости с Pydantic v2
        response = self._make_request(endpoint, method='POST', json_data=request_data.model_dump())
        print(request_data.model_dump())
        if response and "signature" in response:
            return SharkPaySignatureResponse(**response)
        else:
            raise ValueError("Invalid response from SharkPay signature generation.")

    def signature_verify(self, paydesk_id: int, way: str, order_id: str, client_email: str, price: float, currencyCode: str, url: str, signature: str) -> SharkPaySignatureResponse:
        endpoint = "/api/payments/signature/verify"
        request_data = {
            "data": {
                "paydeskId": paydesk_id,
                "way": way,
                "orderId": order_id,
                "clientEmail": client_email,
                "price": price,
                "currencyCode": currencyCode,
                "url": url
            },
            "signature": signature
        }

        # Используем model_dump вместо dict для совместимости с Pydantic v2
        response = self._make_request(endpoint, method='POST', json_data=request_data)
        #print(response)


    def get_payment_offers(self, paymentTypeId: int, paydesk_id: int, way: str, order_id: str, client_email: str, price: float, currencyCode: str, url: str, signature: str) -> Tuple[bool, PaymentOffersResponse]:
        endpoint = "/api/payments/offers/find"
        request_data = {
            "paymentTypeId": paymentTypeId,
            "data": {
                "paydeskId": paydesk_id,
                "way": way,
                "orderId": order_id,
                "clientEmail": client_email,
                "price": price,
                "currencyCode": currencyCode,
                "url": url
            },
            "signature": signature
        }

        # Для отладки, выведите отправляемые данные:
        #print("Request data for offers:", request_data)

        response = self._make_request(endpoint, method='POST', json_data=request_data)
        
        if response and "paymentOffer" in response and "paymentId" in response and "timeLimit" in response:
            return True, PaymentOffersResponse(**response)
        else:
            if not response: return False, None
            return False, response


    def confirm(self, payment_id, signature):
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {signature}'
        }
        endpoint = f"/api/payments/{payment_id}/confirm-offer?lang=ru&url=https://test.klubok-kz.com"
        print("confirm:", payment_id)
        self._make_request(endpoint, method='POST', json_data={}, headers=headers)
        return None

    def cancel(self, payment_id, signature):
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {signature}'
        }
        endpoint = f"/api/payments/{payment_id}/cancel"
        print("cancel:", payment_id)
        self._make_request(endpoint, method='POST', json_data={}, headers=headers)
        return None


    def get_offer(
        self, 
        custom_id: str,
        client_id: str,
        price: float,
        currency: str = "kzt",
    ) -> PaymentOffersResponse: #  Нужен рефактор
        KZTpaymentTypeIds = [11]
        UAHpaymentTypeIds = [7, 6, 1, 2] #  bank ids
        currency = currency.lower()
        match currency:
            case 'kzt':
                for paymentTypeId in KZTpaymentTypeIds:
                    signature_resp = self.generate_signature(
                        paydesk_id=25, # Касса
                        way="sell",
                        order_id=custom_id,
                        client_email=f"{client_id}@sharkpay.team",
                        price=price,
                        currencyCode=currency,
                        url=self.url
                    )
                    signature = signature_resp.signature

                    test = self.signature_verify(
                        paydesk_id=25,
                        way="sell",
                        order_id=custom_id,
                        client_email=f"{client_id}@sharkpay.team",
                        price=price,
                        currencyCode=currency,
                        url=self.url,
                        signature=signature
                    )

                    print("test")
                    print(test)
                    print("test")

                    success, offers = self.get_payment_offers(
                        paymentTypeId=paymentTypeId,
                        paydesk_id=25, # Касса
                        way="sell",
                        order_id=custom_id,
                        client_email=f"{client_id}@sharkpay.team",
                        price=price,
                        currencyCode=currency,
                        url=self.url,
                        signature=signature
                    )
                    if success: return offers
            case 'uah':
                for paymentTypeId in UAHpaymentTypeIds:
                    signature_resp = self.generate_signature(
                        paydesk_id=26, # Касса
                        way="sell",
                        order_id=custom_id,
                        client_email=f"{client_id}@sharkpay.team",
                        price=price,
                        currencyCode=currency,
                        url=self.url
                    )
                    signature = signature_resp.signature

                    self.signature_verify(
                        paydesk_id=26,
                        way="sell",
                        order_id=custom_id,
                        client_email=f"{client_id}@sharkpay.team",
                        price=price,
                        currencyCode=currency,
                        url=self.url,
                        signature=signature
                    )

                    success, offers = self.get_payment_offers(
                        paymentTypeId=paymentTypeId,
                        paydesk_id=26, # Касса
                        way="sell",
                        order_id=custom_id,
                        client_email=f"{client_id}@sharkpay.team",
                        price=price,
                        currencyCode=currency,
                        url=self.url,
                        signature=signature
                    )
                    if success: return offers
            case _:
                return False
        return False


    def check_payment_uploadfile(self, payment_id: int, file: UploadFile, signature: str):
        endpoint = f"/api/payments/{payment_id}/check?url={self.url}"
        # Сигнатура без барера

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {signature}'
        }

        files = {
            'check': (file.filename, file.file, file.content_type)
        }
        response = self._make_request(endpoint, method='POST', files=files, headers=headers)
        return response


if __name__ == "__main__":
    service = SharkPayService('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ODg3LCJpYXQiOjE3MzY1MjM1NTIsImV4cCI6MTczOTExNTU1Mn0.KkSOlGu9OWN8izrcI9Vjc-yr85ylb4jwqmQH50nj_VM')
    #service.confirm(923, 'Wi/TjEYEVl7aSh5QKU6k7wmHNxbethsRrWw8ZRZnJFIpwrZb1hB5pS6f8ecE+7+rMbSuCKXPqOqPliFw/hjlAA==')
    #service.confirm(915, 'XKGI7cWnYwYj3Z+mSXPvPX0Uh3jKaLTJ+XT+44t38w4V1AWcYYnDUxiVyHU+Vphn1wLeP5vPlHd9bOBem1zrDA==')
    #exit()
    result = service.get_offer(
        custom_id='44',
        client_id='1',
        price=3000,
        currency='kzt'
    )
    print(result)
    #exit() # ця сігнатура 
    #signature_resp = service.generate_signature(
    #    paydesk_id=25,
    #    way="sell",
    #    order_id="48",
    #    client_email="1@sharkpay.team",
    #    price=5000,
    #    currencyCode='kzt',
    #    url="https://test.klubok-kz.com"
    #)
    #signature = signature_resp.signature
    #print("Сигнатура:", signature)

    #service.signature_verify(
    #    paydesk_id=25,
    #    way="sell",
    #    order_id="48",
    #    client_email="1@sharkpay.team",
    #    price=5000,
    #    currencyCode='kzt',
    #    url="https://test.klubok-kz.com",
    #    signature=signature
    #)


    #success, offers = service.get_payment_offers(
    #    paymentTypeId=11, # 11 kzt 1 privat
    #    paydesk_id=25,
    #    way="sell",
    #    order_id="48",
    #    client_email="1@sharkpay.team",
    #    price=5000,
    #    currencyCode='kzt',
    #    url="https://test.klubok-kz.com",
    #    signature=signature
    #)

    #print("Реквизиты оплаты:", offers)

    #service.confirm(offers.paymentId, signature)
