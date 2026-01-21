import sqlite3
from datetime import datetime
from config import DATABASE_PATH
from typing import List, Optional, Dict

def get_connection():
    """Получить соединение с БД"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица товаров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock TEXT,
            product_type TEXT DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица заказов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            payment_id TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# === ТОВАРЫ ===

def add_product(name: str, description: str, price: float, stock: str = "", product_type: str = "text") -> int:
    """Добавить товар"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price, stock, product_type) VALUES (?, ?, ?, ?, ?)",
        (name, description, price, stock, product_type)
    )
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id

def get_all_products() -> List[Dict]:
    """Получить все товары"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def get_product(product_id: int) -> Optional[Dict]:
    """Получить товар по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_product(product_id: int, name: str = None, description: str = None, 
                   price: float = None, stock: str = None, product_type: str = None):
    """Обновить товар"""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if price is not None:
        updates.append("price = ?")
        params.append(price)
    if stock is not None:
        updates.append("stock = ?")
        params.append(stock)
    if product_type is not None:
        updates.append("product_type = ?")
        params.append(product_type)
    
    if updates:
        params.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()

def delete_product(product_id: int):
    """Удалить товар"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def get_stock_item(product_id: int) -> Optional[str]:
    """Получить один товар из стока"""
    product = get_product(product_id)
    if not product or not product['stock']:
        return None
    
    stock_lines = product['stock'].strip().split('\n')
    if not stock_lines or stock_lines[0] == '':
        return None
    
    item = stock_lines[0]
    remaining_stock = '\n'.join(stock_lines[1:])
    
    update_product(product_id, stock=remaining_stock)
    return item

# === ЗАКАЗЫ ===

def create_order(user_id: int, username: str, product_id: int, 
                 product_name: str, price: float, payment_id: str) -> int:
    """Создать заказ"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO orders (user_id, username, product_id, product_name, price, payment_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, username, product_id, product_name, price, payment_id)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_order_by_payment(payment_id: str) -> Optional[Dict]:
    """Получить заказ по ID платежа"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE payment_id = ?", (payment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_order_status(payment_id: str, status: str):
    """Обновить статус заказа"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = ? WHERE payment_id = ?",
        (status, payment_id)
    )
    conn.commit()
    conn.close()

def get_all_orders() -> List[Dict]:
    """Получить все заказы"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders

def get_orders_stats() -> Dict:
    """Получить статистику заказов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Общая выручка
    cursor.execute("SELECT SUM(price) FROM orders WHERE status = 'paid'")
    total_revenue = cursor.fetchone()[0] or 0
    
    # Количество заказов
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'")
    total_orders = cursor.fetchone()[0]
    
    # Популярные товары
    cursor.execute("""
        SELECT product_name, COUNT(*) as count, SUM(price) as revenue
        FROM orders 
        WHERE status = 'paid'
        GROUP BY product_name
        ORDER BY count DESC
        LIMIT 5
    """)
    top_products = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'top_products': top_products
    }

# === ПОЛЬЗОВАТЕЛИ ===

def add_user(user_id: int, username: str = None, first_name: str = None, 
             last_name: str = None):
    """Добавить пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
           VALUES (?, ?, ?, ?)""",
        (user_id, username, first_name, last_name)
    )
    conn.commit()
    conn.close()