import requests
import time
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from fastapi import UploadFile, HTTPException
from utils.bot_sender import send_log

class PaymentData(BaseModel):
    rate: float
    amount: float
    currency: str
    card_number: str
    card_holder: str
    bank_name: str
    payment_system_type: str
    invoice_id: int

class PaymentResponse(BaseModel):
    status: int
    data: PaymentData


class PayportService:
    def __init__(self, api3_key, api5_key, api_url, call_back_url) -> None:
        self._api_v3 = api3_key
        self._api_v5 = api5_key
        self._api_url = api_url
        self._callback_url = call_back_url
    

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
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None


    def get_balance(self):
        endpoint = "/api/v5/balance"
        headers = {
            'Authorization': f"Bearer {self._api_v5}"
        }
        return self._make_request(endpoint, 'GET', headers)


    def get_balance_fiat(self):
        endpoint = "/api/v5/fiat-balances"
        headers = {
            'Authorization': f"Bearer {self._api_v5}"
        }
        return self._make_request(endpoint, 'GET', headers)


    def get_amount_limits(self):
        endpoint = "/api/v5/amount-limits"
        headers = {
            'Authorization': f"Bearer {self._api_v5}"
        }
        return self._make_request(endpoint, 'GET', headers)

    
    def request_payment(self, amount, currency="UAH", exact_currency=True, client_expense=0):
        endpoint = "/api/v3/payment/request"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        data = {
            "amount": amount,
            "currency": currency,
            "exact_currency": exact_currency,
            "client_expense": client_expense,
            "locale": "ru"
        }
        response_data = self._make_request(endpoint, 'POST', headers, json_data=data)
        return response_data


    def payment_history(self, status=2):
        '''Возвращает за последние 30 дней'''
        endpoint = "/api/v3/payment/invoices"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        
        # Текущее время в UTC в миллисекундах
        to_date = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # Время 30 дней назад в UTC в миллисекундах
        from_date = to_date - 30 * 24 * 60 * 60 * 1000
        
        # Для отладки: вывод временных меток
        print(f"from_date (ms): {from_date}, to_date (ms): {to_date}")
        
        data = {
            "status": status,
            "from_date": from_date,
            "to_date": to_date,
            "locale": "ru"
        }
        
        response = self._make_request(endpoint, 'POST', headers, json_data=data)
        
        # Для отладки: вывод ответа
        print(f"Response: {response}")
        
        return response


    def request_payment_with_rate(self, amount, currency="USD", exact_currency=True, currency2currency=False, client_expense=0, filter_payment_system_types=None, filter_payment_systems=None, customer_id=None, cross_border=None, cross_border_fiats=None, locale="ru"):
        """
        Запрос на оплату с курсом через API /api/v3/payment/request_with_rate
        """
        endpoint = "/api/v3/payment/request_with_rate"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        data = {
            "amount": amount,
            "currency": currency,
            "exact_currency": exact_currency,
            "currency2currency": currency2currency,
            "client_expense": client_expense,
            "filter_payment_system_types": filter_payment_system_types or [],
            "filter_payment_systems": filter_payment_systems or [],
            "customer_id": customer_id,
            "cross_border": cross_border,
            "cross_border_fiats": cross_border_fiats or [],
            "locale": locale
        }

        return self._make_request(endpoint, 'POST', headers, json_data=data)


    def create_invoice(self, ad_id, amount, currency="USD", locale="ru", client_customer_id=None):
        """Создание инвойса на оплату через API /api/v3/payment/create"""
        endpoint = "/api/v3/payment/create"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        data = {
            "ad_id": ad_id,
            "amount": amount,
            "currency": currency,
            "server_url": self._callback_url,
            "locale": locale,
            "customer_id": client_customer_id,
            "currency2currency": 1,
            "client_expense": 0
        }
        return self._make_request(endpoint, 'POST', headers, json_data=data)


    def payment_check(self, invoice_id):
        """Создание инвойса на оплату через API /api/v3/payment/create"""
        endpoint = "/api/v3/payment/check/approved"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        data = {
            "invoice_id": invoice_id,
            "locale": "ru"
        }
        return self._make_request(endpoint, 'POST', headers, json_data=data)


    def handle_callback(self, callback_data):
        """ Обработка данных из колбэков. callback_data ожидается в виде dict """
        if 'status' in callback_data:
            if callback_data['status'] == 1:
                print(f"Invoice {callback_data['invoice_id']} is paid.")
            elif callback_data['status'] == -1:
                print(f"Invoice {callback_data['invoice_id']} was canceled.")
            elif callback_data['status'] == 3:
                print(f"Invoice {callback_data['invoice_id']} was confirmed by trader.")
        return callback_data


    def cancel_invoice(self, invoice_id, locale='ru'):
        """Отмена инвойса по его ID"""
        endpoint = "/api/v3/payment/cancel"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        data = {
            "invoice_id": invoice_id,
            'locale': locale
        }
        return self._make_request(endpoint, 'POST', headers, json_data=data)


    def make_order(self, amount: float, currency: str, client_customer_id: str) -> PaymentData:
        """
        Проверяет есть ли банк с соответствующими лимитами. 
        Если есть, создает ордер и проверяет статус инвойса.
        """
        if not currency in ['UAH', 'KZT']:
            raise HTTPException(400, "This currency is not active.")
        if currency == 'KZT' and amount < 5000:
            raise HTTPException(400, "Сумма депозита должна быть не меньше 5000.")
        # Получаем доступные методы оплаты
        payments_method = self.request_payment(amount=amount, currency=currency)
        
        # Инициализируем переменные для хранения информации о банках
        selected_bank = None

        try:
            # Ищем подходящий банк
            for payment in payments_method['data']:
                bank_name = payment['bank_name'].lower()  # Приводим к нижнему регистру для удобства сравнения

                if 'pumb' in bank_name in bank_name and not selected_bank:
                    selected_bank = payment
                    break
                elif 'Kaspi' in bank_name in bank_name and not selected_bank:
                    selected_bank = payment
                    break
                elif 'izi bank' in bank_name in bank_name and not selected_bank:
                    selected_bank = payment
                    break
                elif 'ощадбанк' in bank_name in bank_name and not selected_bank:
                    selected_bank = payment
                    break
                elif 'a-bank' in bank_name in bank_name and not selected_bank:
                    selected_bank = payment
                    break
                elif 'privatbank' in bank_name in bank_name and not selected_bank:
                    selected_bank = payment
                    break
                elif 'monobank' in bank_name and not selected_bank:
                    selected_bank = payment
                    break
                else:
                    selected_bank = payment

            if selected_bank:
                # Если банк найден, создаем инвойс
                order = self.create_invoice(
                    ad_id=selected_bank['ad_id'],
                    amount=amount,
                    currency=currency,
                    client_customer_id=str(client_customer_id)
                )

                # Проверяем статус созданного инвойса через payment_check
                if order.get('status') == 1:
                    invoice_id = order['data']['invoice_id']
                    payment_status = self.payment_check(invoice_id)
                    payment_status['data']['invoice_id'] = invoice_id
                    return PaymentData(**payment_status['data'])
                else:
                    raise ValueError(f"Failed to create invoice: {order}")

            else:
                raise ValueError("No suitable bank found.")

        except KeyError:
            raise ValueError("Invalid response format: missing 'data' in response.")
        except Exception as e:
            raise ValueError(f"Error processing payment: {e}")


    def add_receipt(self, invoice_id: int, document: UploadFile):
        """Добавить чек к инвойсу."""
        endpoint = "/api/v3/payment/confirm"  # Или "/api/v3/payment/add-receipt" в зависимости от API
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        data = {
            'invoice_id': int(invoice_id)
        }
        files = {
            'document': (document.filename, document.file, document.content_type)
        }
        return self._make_request(endpoint, 'POST', headers=headers, data=data, files=files)


    def payment_withdraw_list(self, amount: float, currency: str):
        """Создание инвойса на оплату через API /api/v3/withdrawal/request"""
        endpoint = "/api/v3/withdrawal/request"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        data = {
            "amount": amount,
            "currency": currency,
            "merchant_expense": 0,
            "exact_currency": 1
        }
        data = self._make_request(endpoint, 'POST', headers, json_data=data)
        return data


    def payment_withdraw(self, amount, currency, card_to):
        """Создание инвойса на оплату через API /api/v3/payment/create"""
        endpoint = "/api/v3/withdrawal/create"
        headers = {
            'Authorization': f"Bearer {self._api_v3}"
        }
        withdraw_list = self.payment_withdraw_list(amount, currency)
        ad_id = None
        for x in withdraw_list['data']['ads']:
            ad_id = x['ad_id']

        if not ad_id:
            return False
        data = {#81887
            "ad_id": ad_id,
            "amount": amount,
            "currency": currency,
            "merchant_expense": 1,
            "message": card_to,
            "locale": "ru",
            "server_url": self._callback_url
        }
        result = self._make_request(endpoint, 'POST', headers, json_data=data) #invoice_id
        return result


'''
payport = PayportService(
    "a3HXvOjlRP9pmpD2Oxo3TOSbmW3u7hrXBemFxlZWeKMeO03lVHvDQbccrsJIbz3CcZV5jfebyAwgmI2axSgNfLaR5Xord6MfW90TD6mx9M1hDXfL9RjHKWDD4xFnhL5F", 
    "ByBolSx0KzV11x2PJFk8DJenpYVNaIAvAuP3GyrGtqTOGei8ePDpY0OoH6ro75vtBXBQIlvwAMszcXM6j41InEZnwYRsulVzirKeHgns52wFLU6BR3wzKImBKm8G9eit",
    call_back_url='https://cms.clubgg.com.ua/' + 'api/webhook/payport'
).payment_withdraw(52, 'UAH', 5457082257175922)
'''