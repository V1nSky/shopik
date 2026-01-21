import uuid
import requests
import base64
from config import YUKASSA_TOKEN, YUKASSA_SHOP_ID

def create_payment(amount: float, description: str, return_url: str = None) -> dict:
    """
    Создать платеж в ЮKassa
    
    Args:
        amount: Сумма платежа
        description: Описание платежа
        return_url: URL для возврата после оплаты
    
    Returns:
        dict с данными платежа (id, confirmation_url)
    """
    url = "https://api.yookassa.ru/v3/payments"
    
    # Генерация уникального ключа идемпотентности
    idempotence_key = str(uuid.uuid4())
    
    # Базовая аутентификация
    auth_string = f"{YUKASSA_SHOP_ID}:{YUKASSA_TOKEN}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Idempotence-Key": idempotence_key,
        "Authorization": f"Basic {auth_base64}"
    }
    
    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url or "https://t.me/your_bot"
        },
        "capture": True,
        "description": description
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return {
            "payment_id": data["id"],
            "confirmation_url": data["confirmation"]["confirmation_url"],
            "status": data["status"]
        }
    else:
        raise Exception(f"Ошибка создания платежа: {response.text}")

def check_payment(payment_id: str) -> dict:
    """
    Проверить статус платежа
    
    Args:
        payment_id: ID платежа в ЮKassa
    
    Returns:
        dict со статусом платежа
    """
    url = f"https://api.yookassa.ru/v3/payments/{payment_id}"
    
    auth_string = f"{YUKASSA_SHOP_ID}:{YUKASSA_TOKEN}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {auth_base64}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return {
            "payment_id": data["id"],
            "status": data["status"],
            "paid": data["paid"],
            "amount": float(data["amount"]["value"])
        }
    else:
        raise Exception(f"Ошибка проверки платежа: {response.text}")