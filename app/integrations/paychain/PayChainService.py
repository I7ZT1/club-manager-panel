import requests

class PayChainService:
    def __init__(self, api_key: str, api_url: str = 'https://api.paychain.fund/') -> None:
        self._api_key = api_key
        self._api_url = api_url

    def make_headers(self) -> dict:
        headers = {
            'Content-Type': "application/json",
            'x-api-key': self._api_key
        }
        return headers


    def _make_request(self, endpoint, method='GET', headers=None, params=None, json_data=None, data=None, files=None):
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
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=json_data, timeout=10)
            print("--------------------------------")
            print(f"Ответ запроса: {response.status_code}, Text: {response.text}")
            try:
                print(f"Ответ запроса: {response.status_code}, Json: {response.json()}")
            except:
                pass
            print("--------------------------------")
            print(f"payload: {json_data} data: {data}")
            print("--------------------------------")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

        
    def create_order(self, external_transaction_id, first_deposit, amount):
        '''url: payment/trading/pay-in'''
        if first_deposit:
            deposit_type = "FTD"
        else:
            deposit_type = "STD"

        body_req = {
            "depositType": deposit_type,
            "transferType": "local",
            "method": "card",
            "fiatAmount": amount,
            "fiatCurrency": "UAH",
            "extra": {
                "externalTransactionId": external_transaction_id,
                "payerInfo": {
                    "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) AppleWebKit/655.1.15 (KHTML, like Gecko) Version/16.4 Mobile/148 Safari/04.1",
                    "ip": "192.168.1.1",
                    "userId": str(external_transaction_id),
                    "fingerprint": "fbb77b9f4265b18538e66cac5a37c6410dc2cdd7f0cddfde6eda25aa10df669b",
                    "registeredAt": 1728388185326
                }
            }
        }
        headers = self.make_headers()
        return self._make_request(
            endpoint="payment/trading/pay-in",
            method="POST",
            headers=headers,
            json_data=body_req
        )


'''
test = PayChainService(
    '-2cec-498c-8966-035f4ce93869-0fefa53d-a93e-426a-9953-f9e60cb37e53-ecb2effd-441c-4e93-bd9a-4d65ae72d984',
)
data = test.create_order(0, 0, 600.25)
print(data)


# RESPONSE 
{"id": "125aa3c6-319f-44ea-a823-c30f3276e290", 
"fiatAmount": "550.00", "merchantFee": "825826", 
"type": "pay-in", "status": "closed", 
"bank": "UA_PRIVAT_BANK", "fiatCurrency":
 "UAH", "cryptoCurrency": "usdt", 
 "cryptoNetwork": "trc20", 
 "disputeMerchantCheckUrl": null, 
 "externalAppealId": null, 
 "disputeTraderCheckUrl": null, 
 "externalTransactionId": "txn_12556", 
 "cascadeExternalTransactionId": null, 
 "disputeMerchantFiatAmount": "0.00", 
 "transactionWindowInMin": 15, 
 "disputeTraderFiatAmount": "0.00", 
 "disputeTraderDeclineReason": null, 
 "requisite": {"id": "735e085e-5890-47ae-815a-7d3f23b5d69e", 
 "bank": "Privat Bank", "link": null, 
 "ownerName": "Михайлюта Дарья Дмитриевна", 
 "sbpNumber": null, "requisites": "5457082517758400", 
 "crossBorder": false, "fiatCurrency": "UAH", 
 "accountNumber": null}, 
 "cancelReason": "NONE", 
 "method": "card", 
 "extra": {"payerInfo": {"ip": "192.168.1.1", 
 "userId": "00110", "userAgent": 
 "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) 
 AppleWebKit/655.1.15 (KHTML, like Gecko) 
 Version/16.4 Mobile/148 Safari/04.1", 
 "fingerprint": "fbb37c6410dc2cdd7f0cddfde6eda25aa10df669b", 
 "registeredAt": 1728388185326}, 
 "externalTransactionId": "txn_12556"}, 
 "userId": "d82dbbb2-b88e-4796-a760-dc422f2504b8", 
 "merchantId": "13b99dd4-d283-4bb1-9011-c5e6abea5dce", 
 "disputeCreatedAt": null, "cascadeId": null, 
 "createdAt": "2025-07-25T10:58:58.323Z", "cryptoAmount": "12705013", 
 "currencyRate": "43.29"}


{
  "id": "9f86a944-9b44-4362-9ceb-9d4b823dddab",
  "fiatAmount": "1000.24",
  "merchantFee": "1500822",
  "type": "pay-in",
  "status": "active",
  "bank": "UA_PRIVAT_BANK",
  "fiatCurrency": "UAH",
  "cryptoCurrency": "usdt",
  "cryptoNetwork": "trc20",
  "disputeMerchantCheckUrl": null,
  "externalAppealId": null,
  "disputeTraderCheckUrl": null,
  "externalTransactionId": "tr_id",
  "cascadeExternalTransactionId": null,
  "disputeMerchantFiatAmount": "0.00",
  "transactionWindowInMin": 15,
  "disputeTraderFiatAmount": "0.00",
  "disputeTraderDeclineReason": null,
  "requisite": {
    "id": "735e085e-5890-47ae-815a-7d3f23b5d69e",
    "bank": "Privat Bank",
    "link": null,
    "ownerName": "Михайлюта Дарья Дмитриевна",
    "sbpNumber": null,
    "requisites": "5457082517758400",
    "crossBorder": false,
    "fiatCurrency": "UAH",
    "accountNumber": null
  },
  "cancelReason": "NONE",
  "method": "card",
  "extra": {
    "payerInfo": {
      "ip": "192.168.1.1",
      "userId": "65535",
      "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) AppleWebKit/655.1.15 (KHTML, like Gecko) Version/16.4 Mobile/148 Safari/04.1",
      "fingerprint": "fbb77b9f4265b18538e66cac5a37c6410dc2cdd7f0cddfde6eda25aa10df669b",
      "registeredAt": 1728388185326
    },
    "externalTransactionId": "tr_id"
  },
  "userId": "d82dbbb2-b88e-4796-a760-dc422f2504b8",
  "merchantId": "13b99dd4-d283-4bb1-9011-c5e6abea5dce",
  "disputeCreatedAt": null,
  "cascadeId": null,
  "createdAt": "2025-07-25T11:19:16.760Z",
  "cryptoAmount": "23089567",
  "currencyRate": "43.32",
  "externalPaymentPageUrl": "https://pay.paychain.fund/payment?trade=9f86a944-9b44-4362-9ceb-9d4b823dddab",
  "externalAcquiringPaymentPageUrl": "https://pay.paychain.fund/payment-acquiring?trade=9f86a944-9b44-4362-9ceb-9d4b823dddab"
}
'''