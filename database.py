import aiosqlite
import datetime
import random
import string

DB_NAME = "xkart.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_admin BOOLEAN DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                x_username TEXT,
                plan_id TEXT,
                tx_hash TEXT,
                status TEXT,
                created_at TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        await db.commit()
        
        # Safe migrations: add columns if they don't exist
        columns_to_add = [
            ("last_active", "TIMESTAMP"),
            ("clicks_prices", "INTEGER DEFAULT 0"),
            ("clicks_details", "INTEGER DEFAULT 0"),
            ("clicks_event", "INTEGER DEFAULT 0"),
            ("orders_started", "INTEGER DEFAULT 0"),
            ("orders_completed", "INTEGER DEFAULT 0")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass # Column already exists
        await db.commit()

async def add_user(user_id, username, first_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        await db.commit()

async def track_activity(user_id, action=None):
    async with aiosqlite.connect(DB_NAME) as db:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if action in ["clicks_prices", "clicks_details", "clicks_event", "orders_started", "orders_completed"]:
            await db.execute(f'''
                UPDATE users SET last_active = ?, {action} = COALESCE({action}, 0) + 1 WHERE user_id = ?
            ''', (now, user_id))
        else:
            await db.execute('''
                UPDATE users SET last_active = ? WHERE user_id = ?
            ''', (now, user_id))
        await db.commit()

async def create_order(user_id, x_username, plan_id, tx_hash):
    date_str = datetime.datetime.now().strftime("%m%d")
    random_digits = ''.join(random.choices(string.digits, k=4))
    order_id = f"XR{date_str}{random_digits}"
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO orders (order_id, user_id, x_username, plan_id, tx_hash, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, user_id, x_username, plan_id, tx_hash, 'Processing', datetime.datetime.now()))
        await db.commit()
    return order_id

async def get_order(order_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)) as cursor:
            return await cursor.fetchone()

async def update_order_status(order_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE orders SET status = ? WHERE order_id = ?', (status, order_id))
        await db.commit()

async def set_admin(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))
        await db.commit()

async def get_admins():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id FROM users WHERE is_admin = 1') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_user_orders(user_id, limit=5):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT order_id, plan_id, status, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?', (user_id, limit)) as cursor:
            return await cursor.fetchall()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, username, first_name, last_active, orders_started, orders_completed FROM users') as cursor:
            return await cursor.fetchall()

async def get_global_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT 
                SUM(COALESCE(orders_started, 0)), 
                SUM(COALESCE(orders_completed, 0)),
                SUM(COALESCE(clicks_prices, 0)),
                SUM(COALESCE(clicks_details, 0)),
                SUM(COALESCE(clicks_event, 0))
            FROM users
        ''') as cursor:
            return await cursor.fetchone()

async def get_setting(key, default=None):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT value FROM settings WHERE key = ?', (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default

async def set_setting(key, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        await db.commit()

async def get_pending_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT order_id, x_username, plan_id, tx_hash, created_at FROM orders WHERE status = "Pending" OR status = "Processing" ORDER BY created_at ASC') as cursor:
            return await cursor.fetchall()
