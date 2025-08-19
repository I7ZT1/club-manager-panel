from integrations.onepayment.OnePaymentService import OnePaymentsService, DepositSchema
from integrations.payport.PayportService import PayportService, PaymentResponse, PaymentData
from integrations.paybridge.PayBridgeService import PayBridgeService, PayBridgeDepositSchema
from integrations.paychain.PayChainService import PayChainService
from integrations.platipays.PlatiPaysService import PlatiPaysService
from integrations.profita.ProfiatService import ProfiatService

from core.config import settings
from pydantic import BaseModel
from fastapi import HTTPException
from typing import Optional
from enum import Enum


class PaymentProvider(Enum):
    """Платежные провайдеры и их ID в системе биллинга"""
    ONEPAYMENT_KZT = ("onepayment_kzt", 117)
    ONEPAYMENT_UA = ("onepayment_ua", 118)
    PAYPORT_UA = ("payport_ua", 10)
    PAYPORT_KZ = ("payport_kz", 11)
    PAYBRIDGE = ("paybridge", 115)
    PAYCHAIN = ("paychain", 144)
    PLATIPAY = ("platipay", 144)  # Дублирует PayChain - нужно уточнить
    PROFIAT = ("profiat", 147)
    
    def __init__(self, name: str, billing_id: int):
        self.provider_name = name
        self.billing_id = billing_id


class PaymentRequisitesSchema(BaseModel):
    billing_bank: str
    card_to: str
    card_to_details: str
    billing_order_id: Optional[int] = None
    billing_status: Optional[str] = None
    billing_id: Optional[int] = None


paybridge_service_ua = PayBridgeService(
    api_url=settings.PAYBRIDGE_API_URL, 
    merchant_id=settings.PAYBRIDGE_MERCHANT_ID, 
    api_secret=settings.PAYBRIDGE_API_SECRET
)

paychain_service = PayChainService(settings.PAYCHAINT_API_KEY, settings.PAYCHAINT_API_URL)

platipay_service = PlatiPaysService(callback_url=settings.PLATI_PAYS_CALLBACK, APIKEY=settings.PLATI_PAYS_KEY, secret_key=settings.PLATI_PAYS_SECRET) # TODO: TOD

profiat_service = ProfiatService(
    host=settings.PROFIAT_HOST,
    kid=settings.PROFIAT_UID,
    private_key_b64=settings.PROFIAT_KEY
)

onepayment_service_kz = OnePaymentsService(
    api_key=settings.ONEPAYMENT_API_KEY_KZ,
    hook_url=settings.ONEPAYMENT_HOOK_URL_KZ,
    api_url=settings.ONEPAYMENT_API_URL_KZ
)

def get_requisites_from_onepayment_kzt(amount, currency, amo_id, transaction_id=None) -> tuple[str, str, str, int, int, int]:
    data_payment = DepositSchema(
        payment_system="Kaspi Bank",
        national_currency_amount=amount,
        national_currency=currency,
        client_merchant_id=str(amo_id),
        external_order_id=str(transaction_id),
        callback_url=settings.ONEPAYMENT_HOOK_URL_KZ,
        trusted_traffic=True,
        finger_print=str(amo_id)
    )
    order_data = onepayment_service_kz.create_order(data_payment)
    if order_data == 422:
        data_payment.payment_system = None
        order_data = onepayment_service_kz.create_order(data_payment)
    billing_bank = order_data.payment_system
    card_to = order_data.card_number
    card_to_details = order_data.card_owner_name
    return billing_bank, card_to, card_to_details, 0, order_data.uuid, PaymentProvider.ONEPAYMENT_UA.billing_id

def get_requisites_from_payport_ua(amount, currency, amo_id, transaction_id=None) -> tuple[str, str, str, int, int, int]:
    payport_data = PayportService(
        settings.PAYPORT_API3_KEY, 
        settings.PAYPORT_API5_KEY,
        settings.PAYPORT_API_URL,
        settings.PAYPORT_HOOK_URL
    ).make_order(
        amount=amount,
        currency=currency,
        client_customer_id=amo_id
    )
    return payport_data.bank_name, payport_data.card_number, payport_data.card_holder, payport_data.invoice_id, payport_data.invoice_id, PaymentProvider.PAYPORT_UA.billing_id

def get_requisites_from_paybridge(amount, currency, amo_id, transaction_id=None) -> tuple[str, str, str, int, str, int]:
    deposit_data = PayBridgeDepositSchema(
        amount=amount,
        order_id=str(transaction_id),
        currency=currency,
        order_desc=f"Deposit{amount}{currency}by{amo_id}",
        version="1.0"
    )
    order_data = paybridge_service_ua.create_payment(
        deposit_data
    )

    return 'BankName', order_data.card, order_data.card_owner, 0, order_data.payment_id, PaymentProvider.PAYBRIDGE.billing_id

async def get_requisites_from_paychain(amount, currency, amo_id, transaction_id = None):
    try:
        data_paychain = paychain_service.create_order(transaction_id, 0, amount)

        billing_bank = data_paychain["requisite"]["bank"]
        card_to = data_paychain["requisite"]["requisites"]
        card_to_details = data_paychain["requisite"]["ownerName"]
        billing_status = data_paychain["id"]
        return billing_bank, card_to, card_to_details, 0, billing_status, PaymentProvider.PAYCHAIN.billing_id
    except Exception as e:
        raise HTTPException(status_code=402, detail=f"Payment Paychaint processing error: {str(e)}")

async def get_requisites_from_platipay(amount, currency, amo_id, transaction_id = None):
    try:
        data_platipay = platipay_service.create_order(amount, transaction_id, amo_id)

        billing_bank = data_platipay.bank
        card_to = data_platipay.card_number
        card_to_details = ""
        billing_status = data_platipay.bill_id
        return billing_bank, card_to, card_to_details, 0, billing_status, PaymentProvider.PLATIPAY.billing_id
    except Exception as e:
        raise HTTPException(status_code=402, detail=f"Payment Paychaint processing error: {str(e)}")

def get_requisites_from_profiat(amount, currency, amo_id, transaction_id):
    try:
        data_profiat = profiat_service.create_order(amount, currency, amo_id, transaction_id)
        billing_bank = data_profiat.payment.paymethod_description
        card_to = data_profiat.payment.card
        card_to_details = data_profiat.payment.name
        billing_status = data_profiat.payment.id
        return billing_bank, card_to, card_to_details, 0, billing_status, PaymentProvider.PROFIAT.billing_id
    except Exception as e:
        raise HTTPException(status_code=402, detail=f"Payment Paychaint processing error: {str(e)}")

def get_requisites_from_payment_uah(amount, currency, amo_id, transaction_id = None) -> PaymentRequisitesSchema:
    '''Платежки которые участвуют: PayPort, Paybridge, paychain, PlatiPay, Profiat'''
    payment_methods = [
        ("PayBridge", lambda: get_requisites_from_paybridge(amount, currency, amo_id, transaction_id)),
        ("PayPort", lambda: get_requisites_from_payport_ua(amount, currency, amo_id, transaction_id)),
        ("PayChain", lambda: get_requisites_from_paychain(amount, currency, amo_id, transaction_id)),
        ("PlatiPay", lambda: get_requisites_from_platipay(amount, currency, amo_id, transaction_id)),
        ("Profiat", lambda: get_requisites_from_profiat(amount, currency, amo_id, transaction_id)),
    ]


    for payment_name, payment_func in payment_methods:
        try:
            print(f"Пробуем платежку: {payment_name}")
            bank_name, card_number, card_holder, invoice_id, payment_id, payment_billing_id = payment_func()
            
            if bank_name and card_number and card_holder:
                billing_bank = bank_name
                card_to = card_number
                card_to_details = card_holder
                billing_order_id = invoice_id
                billing_status = payment_id #  исторически так сложилось что в статусе лежит UUID
                billing_id = payment_billing_id
                print(f"Успешно получили реквизиты от {payment_name}")
                break
            else:
                print(f"Платежка {payment_name} вернула пустые реквизиты")
        except Exception as e:
            print(f"Ошибка в платежке {payment_name}: {str(e)}")
            continue

    if not card_to:
        raise Exception("Не удалось получить реквизиты ни от одной платежки")

    return PaymentRequisitesSchema(
        billing_bank=billing_bank,
        card_to=card_to,
        card_to_details=card_to_details,
        billing_order_id=billing_order_id,
        billing_status=str(billing_status),
        billing_id=billing_id
    )


#Метод возвращает реквизиты от платежки
def get_requisites_from_payment_kzt(amount, currency, amo_id, transaction_id = None) -> PaymentRequisitesSchema:
    '''Платежки которые участвуют: PayPort, OnePayment'''
    payment_methods = [
        ("OnePayment", lambda: get_requisites_from_onepayment_kzt(amount, currency, amo_id, transaction_id)),
    ]

    for payment_name, payment_func in payment_methods:
        try:
            print(f"Пробуем платежку: {payment_name}")
            bank_name, card_number, card_holder, invoice_id, payment_id, payment_billing_id = payment_func()
            
            if bank_name and card_number and card_holder:
                billing_bank = bank_name
                card_to = card_number
                card_to_details = card_holder
                billing_order_id = invoice_id
                billing_status = payment_id #  исторически так сложилось что в статусе лежит UUID
                billing_id = payment_billing_id
                print(f"Успешно получили реквизиты от {payment_name}")
                break
            else:
                print(f"Платежка {payment_name} вернула пустые реквизиты")
        except Exception as e:
            print(f"Ошибка в платежке {payment_name}: {str(e)}")
            continue

    if not card_to:
        raise Exception("Не удалось получить реквизиты ни от одной платежки")

    return PaymentRequisitesSchema(
        billing_bank=billing_bank,
        card_to=card_to,
        card_to_details=card_to_details,
        billing_order_id=billing_order_id,
        billing_status=str(billing_status),
        billing_id=billing_id
    )


