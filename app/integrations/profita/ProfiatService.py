import base64
import time
import datetime
import random
import json
from typing import Optional, Dict, Any

import requests
import jwt
from pydantic import BaseModel, Field


class ProfiatAuthConfig(BaseModel):
    host: str = Field(default="api.profiat.xyz")
    kid: str
    private_key_b64: str
    # Заранее сконфигурированные пути API согласно документации
    session_jwt_path: str = Field(default="/api/papi/session/jwt/")


class ProfiatCreateOrderRequest(BaseModel):
    # Запрос на создание входящего платежа
    amount: float
    platform: str
    currency: str
    client_id: str
    callback_url: Optional[str] = None
    paymethod: Optional[int] = None
    lesenka: Optional[bool] = None


class PaymentInfo(BaseModel):
    total: float
    fee: float
    fee_native: float
    rate: float
    link: Optional[str] = None
    amount: float
    amount_native: float
    country: Optional[str] = None
    currency: str
    card: Optional[str] = None
    wallet: Optional[str] = None
    name: Optional[str] = None
    operation_id: Optional[int] = None
    id: str
    paymethod: int
    paymethod_description: Optional[str] = None
    status: str
    date_created: int
    timeout: int


class IncomingPaymentProcessingResponse(BaseModel):
    ok: bool
    message: Optional[str] = None
    payment: PaymentInfo


class ProfiatService:
    """
    Клиент Profiat PAPI с аутентификацией через JWT.

    Документация: https://wiki.profiat.xyz/ru/home
    """

    def __init__(
        self,
        host: str,
        kid: str,
        private_key_b64: str,
    ) -> None:
        self._auth = ProfiatAuthConfig(
            host=host,
            kid=kid,
            private_key_b64=private_key_b64,
        )
        self._token: Optional[str] = None
        self._token_exp_at_epoch: int = 0

        pk = self._auth.private_key_b64
        if isinstance(pk, (bytes, bytearray)):
            self._private_key = base64.b64decode(pk)
        else:
            self._private_key = base64.b64decode(str(pk).encode("ascii"))

    def _jwt_claims(self) -> Dict[str, Any]:
        iat = int(time.mktime(datetime.datetime.now().timetuple()))
        # TTL как в рабочем примере: iat + 100 + 60*60
        exp = iat + 100 + 60 * 60
        return {
            "exp": exp,
            "jti": hex(random.getrandbits(12)).upper(),
        }

    def _ensure_session_token(self) -> None:
        now_epoch = int(time.time())
        # Обновляем токен за 60 сек до истечения
        if self._token and now_epoch < (self._token_exp_at_epoch - 60):
            return

        claims = self._jwt_claims()
        jwt_token = jwt.encode(claims, self._private_key, algorithm="RS256")
        # Не декодируем jwt_token в str насильно — requests и сервер принимают bytes или str

        url = f"https://{self._auth.host}{self._auth.session_jwt_path}"
        payload = {"kid": self._auth.kid, "jwt_token": jwt_token}

        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token")
        if not token:
            raise RuntimeError(f"Profait session/jwt error: no token in response {data}")

        self._token = token
        # Токен Profiat – серверный TTL неизвестен: используем claims.exp
        self._token_exp_at_epoch = claims["exp"]

    def _headers(self) -> Dict[str, str]:
        self._ensure_session_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"JWT {self._token}",
        }

    def _request(self, method: str, path: str, json_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"https://{self._auth.host}{path}"
        headers = self._headers()
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        else:
            resp = requests.post(url, headers=headers, json=json_payload, timeout=15)

        # Лог диагностический (при необходимости можно убрать/сменить на logger)
        print("--------------------------------")
        print(f"Request: {method} {url}")
        if json_payload:
            print(f"Payload: {json.dumps(json_payload, ensure_ascii=False)}")
        print(f"Response: {resp.status_code} {resp.text}")
        print("--------------------------------")

        try:
            return resp.json()
        except Exception:
            return {"raw_text": resp.text}


    def create_order(
        self,
        amount: float,
        currency: str,
        client_id: str,
        callback_url: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> IncomingPaymentProcessingResponse:

        callback_url = f"{callback_url}/{order_id}"

        data = {
            'platform': '723f33c7-fc9f-4515-aa38-ef197b295b09',
            'amount': amount,  # Сумма в Песо
            'currency': currency,
            'client_id': client_id,
            'paymethod': 4000,
            'callback_url': callback_url,
            'lesenka': False
        }

        raw = self._request("POST", "/api/papi/incoming/payment/create/processing/", json_payload=data)
        if raw.get("ok") is False:
            raise Exception(f"ProfiatService: create_order error: {raw}")
        return IncomingPaymentProcessingResponse(**raw)


private_key = 'LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlDWUFJQkFBS0JnUURoajFROEdaTWxudDlMenl2Q0JQVWoveWtvZWVqUktuR2laWDNuUUprOCtmOUFucEFYCjdKdHZpMnVVSjIvVG5nY0tLc2ZjcUh0NnJwTzUxYWR0eDIwZXRacGlJNWdoYW5LLzg2ZWt3bGpTakxzMS9tY2cKb2I5cXBRWkVrNWlXNUlURlV4d1lCN1drYWFVdExaT0w5TzNRZDlBWGNDUzFiTStZUVc2TmNDdDJUd0lEQVFBQgpBb0dBWm5hZ3NraC80cWdnRWFVRDRMZzF6K3RhZkF1ZEtsOVlqWWdEUUtqRXM4RnhKWjZpSUd3WVUveUdteCtyCkdmdUFnU3JiN2E0UG9iUnFZUkhmK2JTUDZvZGV4M2I4U2J5azcyRjFnT3NlcW9Gd0pxVnFLOElBSzA4U25FN0MKWGw1amRGTlpZMmpIczhFTlZXYnQxWFlsYjYza3RCNkdPOXdoVFhDemRRSVYvTkVDUlFEcDBJYjN1bEFKdldlVApMbG1YNmpqaEdhN2czNkpORHcvSkdhUFhMWDIxSnFubEpLZnhMT3BKbHBvZCtMTG1idTBGK2JWTVptY1BOZmpvCnY1WXNvTldveVVPcHR3STlBUGIyU3AvdnZHbWxDRlM3UUp0bUNWaVdXSDd2TzZzSHYyelU0TnUvYVFDZlU1eXgKdjJ0N3loNldZMnBXLzNwbTVtTmxyTTltRnUyM1IzVDRLUUpGQU1sRkx4bks4U0VoUVNxcVNJZUVJVWhzVW1UVApQYVExNWZISHQ0a0FhT2pxaW05dEdZQjdtSWFXTkw2K0drcFFqSXFMUk95cWJlYmpJQXhDOStRYzR5OXphV0tMCkFqeFdaeXNLcytTV2paL1JqVVg0V0lXeWtiOWFnYmE5aXRObGIwRlFnTEpxL2xOUmdqcTNqekxTNnNqVGZxYVoKbTRERmkrQWZHOWV2eWF6ZGRxa0NSQXgzOWMwWDdpMVY0a1lzMFlKVlBxcGsvUnJJODFtMlFzVDB6WG50MnBqRwpiMVlXcEVuRDRYZ093RmZvSDhTYmN4NGRmWWNJZ04vSXpiQk9vTDlsS3RHYWNaTnYKLS0tLS1FTkQgUlNBIFBSSVZBVEUgS0VZLS0tLS0K'.encode("ascii")
uid = 'ce54b955-b602-4bd9-96a5-6ec7feae1a5a'
host = 'api.profiat.xyz'

if __name__ == "__main__":
    # Пример использования. Заполните своими значениями из кабинета Profiat.
    service = ProfiatService(
        host=host,
        kid=uid,
        private_key_b64=private_key,
    )

    # Создание ордера (пример)
    data = service.create_order(
        amount=450,
        currency='UAH',
        client_id='1',
        callback_url='https://cms.clubgg.com.ua/api/webhook/test/',
        order_id='order_12345'
    )
    print(data)
