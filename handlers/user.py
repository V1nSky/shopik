from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import (
    get_all_products, get_product, create_order, 
    get_order_by_payment, update_order_status, get_stock_item, add_user
)
from keyboards.user_kb import (
    main_menu_kb, catalog_kb, product_kb, 
    payment_kb, back_to_main_kb
)
from services.payment import create_payment, check_payment

router = Router()

# Тексты (можно выносить в отдельный файл)
START_TEXT = """
👋 <b>Добро пожаловать в наш магазин!</b>

Здесь вы можете приобрести цифровые товары быстро и безопасно.

Выберите действие из меню ниже:
"""

INFO_TEXT = """
ℹ️ <b>Информация о магазине</b>

📦 Мы продаём качественные цифровые товары
💳 Оплата через безопасную платёжную систему
⚡️ Мгновенная выдача товара после оплаты
🔒 Полная конфиденциальность

<b>Правила покупки:</b>
1. Выберите товар из каталога
2. Нажмите "Купить" и оплатите
3. Получите товар автоматически

По всем вопросам: @support
"""

SUPPORT_TEXT = """
📞 <b>Поддержка</b>

Если у вас возникли вопросы или проблемы:

Telegram: @your_support
Email: support@example.com

Время ответа: обычно в течение 1 часа
"""

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    # Сохраняем пользователя в БД
    add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(START_TEXT, reply_markup=main_menu_kb())

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(START_TEXT, reply_markup=main_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать каталог"""
    products = get_all_products()
    
    if not products:
        await callback.message.edit_text(
            "🛒 Каталог пуст. Товары скоро появятся!",
            reply_markup=back_to_main_kb()
        )
    else:
        await callback.message.edit_text(
            "🛒 <b>Каталог товаров</b>\n\nВыберите товар:",
            reply_markup=catalog_kb(products)
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    """Показать товар"""
    product_id = int(callback.data.split("_")[1])
    product = get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    product_type = product.get('product_type', 'text')
    
    if product_type == 'file':
        stock_count = 1 if product['stock'] else 0
        type_text = "📎 Тип: Файл"
    else:
        stock_count = len(product['stock'].split('\n')) if product['stock'] else 0
        type_text = "📝 Тип: Текст/Ключ"
    
    text = f"""
📦 <b>{product['name']}</b>

{product['description']}

{type_text}
💰 Цена: <b>{product['price']} ₽</b>
📊 В наличии: {stock_count} шт.
"""
    
    await callback.message.edit_text(text, reply_markup=product_kb(product_id))
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery):
    """Начать покупку"""
    product_id = int(callback.data.split("_")[1])
    product = get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    # Проверка наличия
    product_type = product.get('product_type', 'text')
    
    if product_type == 'file':
        stock_count = 1 if product['stock'] else 0
    else:
        stock_count = len(product['stock'].split('\n')) if product['stock'] else 0
    
    if stock_count == 0:
        await callback.answer("❌ Товар закончился!", show_alert=True)
        return
    
    try:
        # Создание платежа
        payment_data = create_payment(
            amount=product['price'],
            description=f"Покупка: {product['name']}"
        )
        
        # Сохранение заказа
        create_order(
            user_id=callback.from_user.id,
            username=callback.from_user.username or "Unknown",
            product_id=product_id,
            product_name=product['name'],
            price=product['price'],
            payment_id=payment_data['payment_id']
        )
        
        text = f"""
💳 <b>Оплата заказа</b>

Товар: {product['name']}
Сумма: {product['price']} ₽

Нажмите кнопку ниже для оплаты.
После оплаты нажмите "Проверить оплату" для получения товара.
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=payment_kb(
                payment_data['confirmation_url'],
                payment_data['payment_id']
            )
        )
        
    except Exception as e:
        await callback.answer(f"Ошибка создания платежа: {str(e)}", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery):
    """Проверить оплату"""
    payment_id = callback.data.split("check_payment_")[1]
    
    try:
        # Проверка статуса платежа
        payment_info = check_payment(payment_id)
        
        if payment_info['status'] == 'succeeded' and payment_info['paid']:
            # Получение заказа
            order = get_order_by_payment(payment_id)
            
            if not order:
                await callback.answer("Заказ не найден!", show_alert=True)
                return
            
            if order['status'] == 'paid':
                await callback.answer("✅ Товар уже был выдан!", show_alert=True)
                return
            
            # Получение товара
            product = get_product(order['product_id'])
            
            if not product:
                await callback.answer("❌ Товар не найден!", show_alert=True)
                return
            
            # Проверка типа товара
            if product['product_type'] == 'file':
                # Товар - файл
                item = get_stock_item(order['product_id'])
                
                if not item:
                    await callback.answer("❌ Файлы закончились! Свяжитесь с поддержкой.", show_alert=True)
                    return
                
                # Обновление статуса заказа
                update_order_status(payment_id, 'paid')
                
                # Отправка файла
                try:
                    await callback.message.answer_document(
                        document=item,
                        caption=f"✅ <b>Оплата прошла успешно!</b>\n\nВаш файл: {product['name']}\n\nСпасибо за покупку! 🎉"
                    )
                    await callback.message.edit_text(
                        "✅ Файл отправлен! Проверьте сообщения выше.",
                        reply_markup=back_to_main_kb()
                    )
                except Exception as e:
                    await callback.answer(f"Ошибка отправки файла: {str(e)}", show_alert=True)
                    return
                
            else:
                # Товар - текст/ключ
                item = get_stock_item(order['product_id'])
                
                if not item:
                    await callback.answer("❌ Товар закончился! Свяжитесь с поддержкой.", show_alert=True)
                    return
                
                # Обновление статуса заказа
                update_order_status(payment_id, 'paid')
                
                # Отправка товара
                success_text = f"""
✅ <b>Оплата прошла успешно!</b>

Ваш товар:
<code>{item}</code>

Спасибо за покупку! 🎉
"""
                
                await callback.message.edit_text(success_text, reply_markup=back_to_main_kb())
            
            await callback.answer("✅ Товар получен!", show_alert=True)
            
        elif payment_info['status'] == 'pending':
            await callback.answer("⏳ Платёж в обработке. Подождите немного.", show_alert=True)
        else:
            await callback.answer("❌ Платёж не найден или отменён.", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"Ошибка проверки: {str(e)}", show_alert=True)

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery):
    """Отмена платежа"""
    await callback.message.edit_text(
        "❌ Платёж отменён.",
        reply_markup=back_to_main_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    """Показать информацию"""
    await callback.message.edit_text(INFO_TEXT, reply_markup=back_to_main_kb())
    await callback.answer()

@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    """Показать поддержку"""
    await callback.message.edit_text(SUPPORT_TEXT, reply_markup=back_to_main_kb())
    await callback.answer()