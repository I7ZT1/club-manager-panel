from typing import Optional, Tuple
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
import requests
import time


class SettOrderRequest(BaseModel):
    amount: float
    card: str
    card_details: str
    custom_id: str
    fingerprint: str
    bank: Optional[str] = None
    spb_number: Optional[int] = None
    min_deposit: Optional[float] = 1000
    max_deposit: Optional[float] = None
    bits: Optional[int] = 0
    bits_amount: Optional[int] = 0
    amount_left: Optional[float] = 0
    free_amount: Optional[float] = 0
    webhook_url: str
    currency: str

class OrderResponse(BaseModel):
    status_id: int
    card: str
    card_details: str
    bank: Optional[str]
    spb_number: Optional[int]
    min_deposit: float
    max_deposit: float
    bits: int
    bits_amount: int
    amount: float
    amount_left: float
    reserve_amount: float
    free_amount: float
    complete_amount: float
    currency: str
    custom_id: str
    fingerprint: str
    webhook_url: str
    finish: bool
    id: int
    created_at: datetime
    updated_at: datetime

class TransferRequest(BaseModel):
    amount: float
    spb: bool
    custom_id: str
    fingerprint: str
    time_window: int
    webhook_url: str
    currency: str


class TransferResponse(BaseModel):
    id: int
    trader_order_id: int
    amount: float
    spb: bool
    custom_id: str
    fingerprint: Optional[str]
    time_window: Optional[int]
    webhook_url: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    

class ChangeAmountRequest(BaseModel):
    """Модель запроса для изменения суммы ордера"""
    amount: float


class ChangeStatusRequest(BaseModel):
    """Модель запроса для изменения суммы ордера"""
    status_id: int


def check_available_amount(amount: float, currency: str, player_id: str = None, rating: int = None) -> bool:
    """
    Проверяет доступность указанной суммы через API биллинга.
    
    Args:
        amount: Сумма для проверки
        currency: Код валюты (например, USD, EUR, RUB)
        
    Returns:
        bool: True если сумма доступна, False если недоступна, None в случае ошибки
    """
    try:
        if player_id and rating:
            response = requests.get(
                f'https://billing1.klubok-kz.com/api/v1/info/check-amount/{amount}/{currency.upper()}?finger_print={player_id}&rating={rating}',
                timeout=10
                )
        elif rating:
            response = requests.get(
                f'https://billing1.klubok-kz.com/api/v1/info/check-amount/{amount}/{currency.upper()}?rating={rating}',
                timeout=10
            )
        else:
            response = requests.get(
                f'https://billing1.klubok-kz.com/api/v1/info/check-amount/{amount}/{currency.upper()}',
                timeout=10
            )

        response.raise_for_status()
        
        # Прямой возврат результата как булева значения
        return response.json()
    except Exception as e:
        print(f"Error checking available amount: {e}")
        return None


class SettlementService:
    def __init__(self, api_url: str, auth_token: str):
        self._api_url = api_url.rstrip('/')
        self._auth_token = auth_token
        self._cookies = {
            'auth_token': auth_token,
            'bearer': 'string',
            'Authorization': 'test'
        }

    def create_order(self, order_data: SettOrderRequest) -> Optional[OrderResponse]:
        """
        Create a new order using the provided order data.
        
        Args:
            order_data (SettOrderRequest): The order data to be sent
            
        Returns:
            Optional[OrderResponse]: The validated response from the API if successful, None otherwise
        """
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
            'Origin': self._api_url,
            'Referer': f'{self._api_url}/docs',
        }

        try:
            response = requests.post(
                f'{self._api_url}/api/v1/traders/order',
                headers=headers,
                cookies=self._cookies,
                json=order_data.model_dump(),
                timeout=10
            )
            response.raise_for_status()
            return OrderResponse(**response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error creating order: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None
        except ValueError as e:
            print(f"Error parsing response data: {e}")
            return None


    def finish_order(self, order_id: str) -> Optional[OrderResponse]:
        """
        Retrieve order details by order ID.
        
        Args:
            order_id (str): The ID of the order to retrieve
            
        Returns:
            Optional[OrderResponse]: The validated order details if successful, None otherwise
        """
        headers = {
            'Accept': 'application/json',
        }

        try:
            response = requests.get(
                f'{self._api_url}/api/v1/traders/order/{order_id}/finish',
                headers=headers,
                cookies=self._cookies,
                timeout=10
            )
            response.raise_for_status()
            return OrderResponse(**response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving order: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None
        except ValueError as e:
            print(f"Error parsing response data: {e}")
            return None


    def get_order(self, order_id: str) -> Optional[OrderResponse]:
        """
        Retrieve order details by order ID.
        
        Args:
            order_id (str): The ID of the order to retrieve
            
        Returns:
            Optional[OrderResponse]: The validated order details if successful, None otherwise
        """
        headers = {
            'Accept': 'application/json',
        }

        try:
            response = requests.get(
                f'{self._api_url}/api/v1/traders/order/{order_id}',
                headers=headers,
                cookies=self._cookies,
                timeout=10
            )
            response.raise_for_status()
            return OrderResponse(**response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving order: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None
        except ValueError as e:
            print(f"Error parsing response data: {e}")
            return None

    def create_transfer(self, transfer_data: TransferRequest) -> Optional[TransferResponse]:
        """
        Create a new transfer using the provided data.
        
        Args:
            transfer_data (TransferRequest): The transfer data to be sent
            
        Returns:
            Optional[dict]: The response from the API if successful, None otherwise
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                f'{self._api_url}/api/v1/transfer/make-transfer',
                headers=headers,
                cookies=self._cookies,
                json=transfer_data.model_dump(),
                timeout=10
            )
            response.raise_for_status()
            return TransferResponse(**response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error creating transfer: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None


    def change_order_amount(self, order_id: int, new_amount: float) -> Optional[OrderResponse]:
        """
        Изменить сумму существующего ордера.
        
        Args:
            order_id (int): ID ордера для изменения
            new_amount (float): Новая сумма ордера
            
        Returns:
            Optional[OrderResponse]: Обновленный ордер если успешно, None в случае ошибки
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        data = ChangeAmountRequest(amount=new_amount)
        
        try:
            response = requests.post(
                f'{self._api_url}/api/v1/traders/order/{order_id}/amount',
                headers=headers,
                cookies=self._cookies,
                json=data.model_dump(),
                timeout=10
            )
            response.raise_for_status()
            return OrderResponse(**response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error changing order amount: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None
        except ValueError as e:
            print(f"Error parsing response data: {e}")
            return None


    def change_order_status(self, order_id: int, status_id: int) -> Optional[OrderResponse]:
        """
        Изменить сумму существующего ордера.
        
        Args:
            order_id (int): ID ордера для изменения
            status_id (float): Новый статус
            
        Returns:
            Optional[OrderResponse]: Обновленный ордер если успешно, None в случае ошибки
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        data = ChangeStatusRequest(status_id=status_id)
        
        try:
            response = requests.post(
                f'{self._api_url}/api/v1/traders/order/{order_id}/status',
                headers=headers,
                cookies=self._cookies,
                json=data.model_dump(),
                timeout=10
            )
            response.raise_for_status()
            return OrderResponse(**response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error changing order amount: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None
        except ValueError as e:
            print(f"Error parsing response data: {e}")
            return None


    def sync_order_deposit_status(self, order_id: int, transaction_status_id: int) -> Optional[OrderResponse]:
        """
        Изменить сумму существующего ордера.
        
        Args:
            order_id (int): ID ордера для изменения
            status_id (float): Новый статус
            
        Returns:
            Optional[OrderResponse]: Обновленный ордер если успешно, None в случае ошибки
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        status_id = 0
        
        match transaction_status_id: # FIXME: статус 5 это ошибка, она может возникать в атоматизации поэтому не обрабатываем
            case 11 | 9 | 8 | 7 | 6:
                status_id = 2
            case 4:
                status_id = 4
            case 3:
                status_id = 1
            case _:
                return None

        data = ChangeStatusRequest(status_id=status_id)
        
        try:
            response = requests.post(
                f'{self._api_url}/api/v1/transfer/{order_id}/status',
                headers=headers,
                cookies=self._cookies,
                json=data.model_dump(),
                timeout=10
            )
            response.raise_for_status()
            return OrderResponse(**response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error changing order amount: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Server response: {e.response.text}")
            return None
        except ValueError as e:
            print(f"Error parsing response data: {e}")
            return None

    def create_payment(self, amount: float, currency: str, player_id: str = None, rating: int = None) -> dict:
        """
        Создает новый платеж через API биллинга.
        
        Args:
            amount: Сумма платежа
            currency: Код валюты (например, USD, EUR, RUB)
            player_id: ID игрока (опционально)
            rating: Рейтинг игрока (опционально)
            
        Returns:
            dict: Данные созданного платежа или None в случае ошибки
        """
        try:
            url = f'https://billing1.klubok-kz.com/api/v1/payment/create/{amount}/{currency.upper()}'
            if player_id and rating:
                url += f'?finger_print={player_id}&rating={rating}'
            elif rating:
                url += f'?rating={rating}'
                
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating payment: {e}")
            return None

    def check_payment(self, payment_id: str) -> dict:
        """
        Проверяет статус платежа через API биллинга.
        
        Args:
            payment_id: ID платежа для проверки
            
        Returns:
            dict: Данные платежа или None в случае ошибки
        """
        try:
            response = requests.get(
                f'https://billing1.klubok-kz.com/api/v1/payment/check/{payment_id}',
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error checking payment: {e}")
            return None

    def cancel_payment(self, payment_id: str) -> bool:
        """
        Отменяет платеж через API биллинга.
        
        Args:
            payment_id: ID платежа для отмены
            
        Returns:
            bool: True если платеж успешно отменен, False в случае ошибки
        """
        try:
            response = requests.post(
                f'https://billing1.klubok-kz.com/api/v1/payment/cancel/{payment_id}',
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error canceling payment: {e}")
            return False

    def get_payment_methods(self) -> list:
        """
        Получает список доступных методов оплаты через API биллинга.
        
        Returns:
            list: Список методов оплаты или пустой список в случае ошибки
        """
        try:
            response = requests.get(
                'https://billing1.klubok-kz.com/api/v1/payment/methods',
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting payment methods: {e}")
            return []

    def get_payment_history(self, player_id: str = None) -> list:
        """
        Получает историю платежей через API биллинга.
        
        Args:
            player_id: ID игрока (опционально)
            
        Returns:
            list: Список платежей или пустой список в случае ошибки
        """
        try:
            url = 'https://billing1.klubok-kz.com/api/v1/payment/history'
            if player_id:
                url += f'?player_id={player_id}'
                
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting payment history: {e}")
            return []


'''
# Usage example:

# Initialize the service
service = SettlementService('https://billing1.klubok-kz.com', 'test')

# Create transfer data
transfer_data = TransferRequest(
    amount=1444,
    spb=False,
    custom_id="TRF-123",
    fingerprint="fp_abcd1234",
    time_window=20,
    webhook_url="https://api.example.com/webhook/trf123",
    currency="RUB"
)

# Create a transfer
response = service.create_transfer(transfer_data)
if response:
    print("Transfer created successfully:", response)


# Create order data
order_data = SettOrderRequest(
    amount=1000.0,              # Сумма заказа
    card="4400123456789012",    # Номер карты
    card_details="Test Card",   # Детали карты
    custom_id="ORD-123",        # Ваш уникальный идентификатор заказа
    fingerprint="fp_xyz789",    # Уникальный отпечаток для идентификации
    bank="Kaspi",              # Название банка
    spb_number=123456,         # Номер СПБ
    min_deposit=500.0,         # Минимальная сумма депозита
    max_deposit=5000.0,        # Максимальная сумма депозита
    bits=1024,                 # Биты
    bits_amount=100,           # Количество битов
    amount_left=900.0,         # Оставшаяся сумма
    free_amount=100.0,         # Свободная сумма
    webhook_url="https://api.example.com/webhook/ord123",  # URL для вебхука
    currency="KZT"             # Валюта
)

# Create an order
response = service.create_order(order_data)
if response:
    print("Order created successfully:")
    print(f"Order ID: {response.id}")
    print(f"Status ID: {response.status_id}")
    print(f"Amount: {response.amount} {response.currency}")
    print(f"Created at: {response.created_at}")
else:
    print("Failed to create order")
'''