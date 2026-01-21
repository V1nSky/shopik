from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database.models import (
    add_product, get_all_products, get_product, 
    update_product, delete_product, get_all_orders, get_orders_stats
)
from keyboards.admin_kb import (
    admin_menu_kb, admin_products_kb, admin_product_actions_kb,
    admin_confirm_delete_kb, admin_back_kb
)

router = Router()

# FSM состояния для админки
class AdminStates(StatesGroup):
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_type = State()
    waiting_product_stock = State()
    
    waiting_new_price = State()
    waiting_new_description = State()
    waiting_add_stock = State()

def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    return user_id == ADMIN_ID

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await message.answer(
        "👑 <b>Админ панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu_kb()
    )

@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery):
    """Главное меню админки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👑 <b>Админ панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    """Закрыть админку"""
    await callback.message.delete()
    await callback.answer()

# === ДОБАВЛЕНИЕ ТОВАРА ===

@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text("📝 Введите название товара:")
    await state.set_state(AdminStates.waiting_product_name)
    await callback.answer()

@router.message(AdminStates.waiting_product_name)
async def admin_product_name(message: Message, state: FSMContext):
    """Получение названия товара"""
    await state.update_data(name=message.text)
    await message.answer("📝 Введите описание товара:")
    await state.set_state(AdminStates.waiting_product_description)

@router.message(AdminStates.waiting_product_description)
async def admin_product_description(message: Message, state: FSMContext):
    """Получение описания товара"""
    await state.update_data(description=message.text)
    await message.answer("💰 Введите цену товара (только число):")
    await state.set_state(AdminStates.waiting_product_price)

@router.message(AdminStates.waiting_product_price)
async def admin_product_price(message: Message, state: FSMContext):
    """Получение цены товара"""
    try:
        price = float(message.text)
        await state.update_data(price=price)
        
        # Создаём клавиатуру для выбора типа товара
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Текст/Ключ", callback_data="product_type_text")],
            [InlineKeyboardButton(text="📎 Файл", callback_data="product_type_file")]
        ])
        
        await message.answer(
            "📦 Выберите тип товара:",
            reply_markup=keyboard
        )
        await state.set_state(AdminStates.waiting_product_type)
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число:")

@router.message(AdminStates.waiting_product_stock)
async def admin_product_stock(message: Message, state: FSMContext):
    """Получение стока товара"""
    data = await state.get_data()
    product_type = data.get('product_type', 'text')
    
    if product_type == 'file':
        # Обработка файла
        if message.document:
            file_id = message.document.file_id
            stock = file_id
        elif message.text and message.text.lower() == "пропустить":
            stock = ""
        else:
            await message.answer("❌ Отправьте файл или напишите 'пропустить'")
            return
    else:
        # Обработка текста
        stock = "" if message.text and message.text.lower() == "пропустить" else message.text
    
    # Добавление товара в БД
    product_id = add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        stock=stock,
        product_type=product_type
    )
    
    if product_type == 'file':
        stock_count = 1 if stock else 0
    else:
        stock_count = len(stock.split('\n')) if stock else 0
    
    type_emoji = "📎" if product_type == 'file' else "📝"
    
    await message.answer(
        f"✅ Товар добавлен!\n\n"
        f"ID: {product_id}\n"
        f"Название: {data['name']}\n"
        f"Цена: {data['price']} ₽\n"
        f"Тип: {type_emoji} {product_type}\n"
        f"Товаров: {stock_count} шт.",
        reply_markup=admin_back_kb()
    )
    
    await state.clear()


# Обработчики выбора типа товара
@router.callback_query(F.data == "product_type_text")
async def product_type_text(callback: CallbackQuery, state: FSMContext):
    """Выбран тип: текст"""
    await state.update_data(product_type='text')
    await callback.message.edit_text(
        "📝 Отправьте товары (каждый с новой строки):\n\n"
        "Например:\n"
        "KEY1-XXXX-XXXX\n"
        "KEY2-YYYY-YYYY\n\n"
        "Или отправьте 'пропустить' чтобы добавить позже."
    )
    await state.set_state(AdminStates.waiting_product_stock)
    await callback.answer()


@router.callback_query(F.data == "product_type_file")
async def product_type_file(callback: CallbackQuery, state: FSMContext):
    """Выбран тип: файл"""
    await state.update_data(product_type='file')
    await callback.message.edit_text(
        "📎 Отправьте файл товара:\n\n"
        "Поддерживаемые форматы:\n"
        "• .zip, .rar, .7z - архивы\n"
        "• .exe, .apk - программы\n"
        "• .txt, .pdf, .doc - документы\n"
        "• .mp3, .mp4 - медиа\n"
        "• Любые другие файлы до 50 МБ\n\n"
        "Или отправьте 'пропустить' чтобы добавить позже."
    )
    await state.set_state(AdminStates.waiting_product_stock)
    await callback.answer()

# === УПРАВЛЕНИЕ ТОВАРАМИ ===

@router.callback_query(F.data == "admin_products")
async def admin_products_list(callback: CallbackQuery):
    """Список товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    products = get_all_products()
    
    if not products:
        await callback.message.edit_text(
            "📦 Нет товаров.\n\nИспользуйте 'Добавить товар'",
            reply_markup=admin_back_kb()
        )
    else:
        await callback.message.edit_text(
            "📦 <b>Управление товарами</b>\n\nВыберите товар:",
            reply_markup=admin_products_kb(products)
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_product_"))
async def admin_product_detail(callback: CallbackQuery):
    """Детали товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    product = get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    product_type = product.get('product_type', 'text')
    
    if product_type == 'file':
        stock_count = 1 if product['stock'] else 0
        type_emoji = "📎"
    else:
        stock_count = len(product['stock'].split('\n')) if product['stock'] else 0
        type_emoji = "📝"
    
    text = f"""
📦 <b>{product['name']}</b>

{product['description']}

💰 Цена: {product['price']} ₽
{type_emoji} Тип: {product_type}
📊 В наличии: {stock_count} шт.
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_product_actions_kb(product_id)
    )
    await callback.answer()

# === ИЗМЕНЕНИЕ ЦЕНЫ ===

@router.callback_query(F.data.startswith("admin_edit_price_"))
async def admin_edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начать изменение цены"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)
    
    await callback.message.edit_text("💰 Введите новую цену:")
    await state.set_state(AdminStates.waiting_new_price)
    await callback.answer()

@router.message(AdminStates.waiting_new_price)
async def admin_edit_price_finish(message: Message, state: FSMContext):
    """Сохранение новой цены"""
    try:
        price = float(message.text)
        data = await state.get_data()
        product_id = data['product_id']
        
        update_product(product_id, price=price)
        
        await message.answer(
            f"✅ Цена обновлена: {price} ₽",
            reply_markup=admin_back_kb()
        )
        
        await state.clear()
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число:")

# === ИЗМЕНЕНИЕ ОПИСАНИЯ ===

@router.callback_query(F.data.startswith("admin_edit_desc_"))
async def admin_edit_desc_start(callback: CallbackQuery, state: FSMContext):
    """Начать изменение описания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[3])
    await state.update_data(product_id=product_id)
    
    await callback.message.edit_text("📝 Введите новое описание:")
    await state.set_state(AdminStates.waiting_new_description)
    await callback.answer()

@router.message(AdminStates.waiting_new_description)
async def admin_edit_desc_finish(message: Message, state: FSMContext):
    """Сохранение нового описания"""
    data = await state.get_data()
    product_id = data['product_id']
    
    update_product(product_id, description=message.text)
    
    await message.answer(
        "✅ Описание обновлено",
        reply_markup=admin_back_kb()
    )
    
    await state.clear()

# === ДОБАВЛЕНИЕ СТОКА ===

@router.callback_query(F.data.startswith("admin_add_stock_"))
async def admin_add_stock_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление стока"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[3])
    product = get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    await state.update_data(product_id=product_id)
    
    product_type = product.get('product_type', 'text')
    
    if product_type == 'file':
        await callback.message.edit_text(
            "📎 Отправьте новый файл товара:\n\n"
            "⚠️ Внимание: старый файл будет заменён!"
        )
    else:
        await callback.message.edit_text(
            "📦 Отправьте товары (каждый с новой строки):\n\n"
            "Они будут добавлены к существующему стоку."
        )
    
    await state.set_state(AdminStates.waiting_add_stock)
    await callback.answer()

@router.message(AdminStates.waiting_add_stock)
async def admin_add_stock_finish(message: Message, state: FSMContext):
    """Добавление стока"""
    data = await state.get_data()
    product_id = data['product_id']
    
    product = get_product(product_id)
    
    if not product:
        await message.answer("❌ Товар не найден!", reply_markup=admin_back_kb())
        await state.clear()
        return
    
    product_type = product.get('product_type', 'text')
    
    if product_type == 'file':
        # Обработка файла
        if message.document:
            new_stock = message.document.file_id
            update_product(product_id, stock=new_stock)
            
            await message.answer(
                "✅ Файл обновлён!",
                reply_markup=admin_back_kb()
            )
        else:
            await message.answer(
                "❌ Отправьте файл!",
                reply_markup=admin_back_kb()
            )
    else:
        # Обработка текста
        old_stock = product['stock'] if product['stock'] else ""
        new_stock = old_stock + "\n" + message.text if old_stock else message.text
        
        update_product(product_id, stock=new_stock)
        
        new_count = len(new_stock.split('\n'))
        
        await message.answer(
            f"✅ Сток обновлён!\n\nВсего товаров: {new_count} шт.",
            reply_markup=admin_back_kb()
        )
    
    await state.clear()

# === УДАЛЕНИЕ ТОВАРА ===

@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[2])
    product = get_product(product_id)
    
    await callback.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить товар?\n\n"
        f"<b>{product['name']}</b>\n\n"
        f"Это действие необратимо!",
        reply_markup=admin_confirm_delete_kb(product_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def admin_delete_finish(callback: CallbackQuery):
    """Удаление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[3])
    delete_product(product_id)
    
    await callback.message.edit_text(
        "✅ Товар удалён",
        reply_markup=admin_back_kb()
    )
    await callback.answer()

# === СТАТИСТИКА ===

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    stats = get_orders_stats()
    
    text = f"""
📊 <b>Статистика продаж</b>

💰 Общая выручка: <b>{stats['total_revenue']:.2f} ₽</b>
📦 Всего заказов: <b>{stats['total_orders']}</b>

<b>Популярные товары:</b>
"""
    
    if stats['top_products']:
        for i, product in enumerate(stats['top_products'], 1):
            text += f"\n{i}. {product['product_name']}: {product['count']} шт. ({product['revenue']:.2f} ₽)"
    else:
        text += "\nПока нет продаж"
    
    await callback.message.edit_text(text, reply_markup=admin_back_kb())
    await callback.answer()

# === ЗАКАЗЫ ===

@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    """Показать все заказы"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return
    
    orders = get_all_orders()
    
    if not orders:
        await callback.message.edit_text(
            "📋 Нет заказов",
            reply_markup=admin_back_kb()
        )
        return
    
    text = "📋 <b>Последние заказы</b>\n\n"
    
    for order in orders[:10]:  # Показываем последние 10
        status_emoji = "✅" if order['status'] == 'paid' else "⏳"
        text += f"{status_emoji} {order['product_name']} - {order['price']} ₽\n"
        text += f"   @{order['username']} | {order['created_at'][:16]}\n\n"
    
    await callback.message.edit_text(text, reply_markup=admin_back_kb())
    await callback.answer()