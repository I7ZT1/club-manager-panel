import time
import hashlib
import hmac
import base64
import json
import requests


class WhiteExchangeService:
    def __init__(self, token: str, secret: str, base_url: str = "https://whiteexchange.io") -> None:
        self.token = token
        self.secret = secret.encode("utf-8")
        self.base_url = base_url

    def _make_signature(self, method: str, path: str, body: dict, timestamp: int) -> str:
        body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        message = f"{timestamp}{method}{path}{body_json}".encode("utf-8")
        return hmac.new(self.secret, message, hashlib.sha512).hexdigest()

    def _make_headers(self, method: str, path: str, body: dict) -> dict:
        timestamp = int(time.time())
        signature = self._make_signature(method, path, body, timestamp)

        headers = {
            "X-Timestamp": str(timestamp),
            "X-Signature": signature,
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        return headers

    def _request(self, method: str, path: str, body: dict):
        url = self.base_url + path
        headers = self._make_headers(method, path, body)

        print("📡 Sending request...")
        print("📤 URL:", url)
        print("📤 Method:", method)
        print("📤 Headers:", headers)
        print("📤 Body:", body)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=10
            )
            print("✅ Status:", response.status_code)
            print("📥 Response:", response.text)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print("❌ Request Error:", str(e))
            return None

    def create_invoice(
        self,
        caller_id: str,
        payer_email: str,
        amount: float,
        currency: str = "UAH",
        kind: str = "h2h",
        card_number: str = None,
        card_holder: str = None,
        bank_card_token: str = None,
        bank_card_fingerprint: str = None,
        bank_card_phone: str = None,
        callback_url: str = None
    ):
        """
        POST /api/v1/invoices — Создание инвойса
        """
        path = "/api/v1/invoices"
        body = {
            "caller_id": caller_id,
            "payer_email": payer_email,
            "amount": amount,
            "currency": currency,
            "kind": kind
        }

        if card_number:
            body["bank_card_number"] = card_number
        if card_holder:
            body["bank_card_holder"] = card_holder
        if bank_card_token:
            body["bank_card_token"] = bank_card_token
        if bank_card_fingerprint:
            body["bank_card_fingerprint"] = bank_card_fingerprint
        if bank_card_phone:
            body["bank_card_phone"] = bank_card_phone
        if callback_url:
            body["callback_url"] = callback_url

        return self._request("POST", path, body)

    def update_invoice_status(self, invoice_id: str, status: str = "dispute"):
        """
        PATCH /api/v1/invoices/{invoice_id} — Обновление статуса инвойса
        """
        path = f"/api/v1/invoices/{invoice_id}"
        body = {"status": status}
        return self._request("PATCH", path, body)

    def upload_receipt(self, invoice_id: str, filepath: str, filename: str = "receipt.jpg"):
        """
        POST /api/v1/invoices/{invoice_id}/receipt — Загрузка квитанции
        """
        with open(filepath, "rb") as f:
            file_base64 = base64.b64encode(f.read()).decode("utf-8")

        path = f"/api/v1/invoices/{invoice_id}/receipt"
        body = {
            "filename": filename,
            "body": file_base64
        }
        return self._request("POST", path, body)


data = WhiteExchangeService(
    token="XeVgga12qgR6b1rVcBx3CNID4b0Yc0lguumSQdoQx0HxwU3JJ02EeMqdottvsvOI",
    secret="oi5-aFQCowuwwuhUR9i84WVPCOP9axbH3vxXFrVojXxJ2oxeFwBJBwXKPv4pWmUO",
    base_url="https://whiteexchange.io"
)

print(data.create_invoice(
    caller_id="1234567890",
    payer_email="test@test.com",
    amount=500,
    currency="UAH",
    kind="h2h",
))