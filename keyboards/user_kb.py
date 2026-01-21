from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from typing import List, Dict

def main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
        [InlineKeyboardButton(text="📄 Информация", callback_data="info")],
        [InlineKeyboardButton(text="📞 Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def catalog_kb(products: List[Dict]) -> InlineKeyboardMarkup:
    """Каталог товаров"""
    keyboard = []
    
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} - {product['price']} ₽",
                callback_data=f"product_{product['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def product_kb(product_id: int) -> InlineKeyboardMarkup:
    """Кнопки для конкретного товара"""
    keyboard = [
        [InlineKeyboardButton(text="💳 Купить", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton(text="◀️ К каталогу", callback_data="catalog")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def payment_kb(payment_url: str, payment_id: str) -> InlineKeyboardMarkup:
    """Кнопки для оплаты"""
    keyboard = [
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_main_kb() -> InlineKeyboardMarkup:
    """Кнопка назад в главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)