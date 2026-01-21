from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict

def admin_menu_kb() -> InlineKeyboardMarkup:
    """Админ меню"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📦 Управление товарами", callback_data="admin_products")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 Все заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_products_kb(products: List[Dict]) -> InlineKeyboardMarkup:
    """Список товаров для управления"""
    keyboard = []
    
    for product in products:
        product_type = product.get('product_type', 'text')
        
        if product_type == 'file':
            stock_count = 1 if product['stock'] else 0
            type_emoji = "📎"
        else:
            stock_count = len(product['stock'].split('\n')) if product['stock'] else 0
            type_emoji = "📝"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{type_emoji} {product['name']} ({stock_count} шт.)",
                callback_data=f"admin_product_{product['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_product_actions_kb(product_id: int) -> InlineKeyboardMarkup:
    """Действия с товаром"""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Изменить цену", callback_data=f"admin_edit_price_{product_id}")],
        [InlineKeyboardButton(text="📝 Изменить описание", callback_data=f"admin_edit_desc_{product_id}")],
        [InlineKeyboardButton(text="📦 Загрузить товар", callback_data=f"admin_add_stock_{product_id}")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"admin_delete_{product_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_products")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_confirm_delete_kb(product_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_confirm_delete_{product_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_product_{product_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_back_kb() -> InlineKeyboardMarkup:
    """Кнопка назад в админ меню"""
    keyboard = [
        [InlineKeyboardButton(text="◀️ Админ меню", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)