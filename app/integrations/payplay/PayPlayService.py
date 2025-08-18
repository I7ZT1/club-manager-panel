import requests

class PayPlayService:
    BASE_URL = "https://api.payplay.io"  # обнови, если в доке другой

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def create_order(self, amount: float, currency: str, order_id: str, lang: str) -> str:
        """
        Вернет url
        """
        links = {
            "UA": 'https://t.me/KlubOK_UAbot',
            "KZ": 'https://t.me/KZKlubOK_bot',
        }
        url = f"{self.BASE_URL}/private-api/crypto-topups/klubok"
        payload = {
            "amount": amount,
            "currency": currency,
            "external_order_id": order_id,
            "successful_link": links.get(lang, 'https://t.me/'),
            "failure_link": links.get(lang, 'https://t.me/')
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json().get('order', {}).get('acquiring_url'), resp.json().get('order', {}).get('id')






'''
payplay_service = PayPlay(settings.PAYPLAY_API_KEY)

pp = PayPlay(TOKEN)
order = pp.create_order(
    amount=11,
    currency="USDT",
    order_id="test",  # данные из доки, если нужно
    lang="UA"
)
print(order)
'''