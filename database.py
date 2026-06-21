import sqlite3
import threading

_lock = threading.Lock()
DB_FILE = "bot.db"

def _execute(query, params=(), fetch=None):
    with _lock:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if fetch == "all":
                res = [dict(r) for r in cursor.fetchall()]
            elif fetch == "one":
                row = cursor.fetchone()
                res = dict(row) if row else None
            else:
                conn.commit()
                res = cursor.lastrowid
            return res
        finally:
            conn.close()

def init_db():
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            is_admin INTEGER DEFAULT 0
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS services (
            service_id TEXT,
            country TEXT,
            service_name TEXT,
            service_price REAL,
            is_enabled INTEGER DEFAULT 1,
            is_top INTEGER DEFAULT 0,
            PRIMARY KEY (service_id, country)
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS recharge_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS admin_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
    ]
    for q in queries:
        _execute(q)

    # Initialize settings if not exists
    _execute("INSERT OR IGNORE INTO admin_settings (key, value) VALUES ('upi_id', 'notset@upi')")
    _execute("INSERT OR IGNORE INTO admin_settings (key, value) VALUES ('qr_file_id', '')")
    _execute("INSERT OR IGNORE INTO admin_settings (key, value) VALUES ('qr_text', 'Scan QR to pay')")
    _execute("INSERT OR IGNORE INTO admin_settings (key, value) VALUES ('swiggy_service_id', 'swiggy')")

# ── Logs ───────────────────────────────────────────────────────
def add_log(category, message, user_id=None):
    try:
        _execute("INSERT INTO logs (user_id, category, message) VALUES (?, ?, ?)",
                 (user_id, category, message))
    except Exception:
        pass

def get_logs(limit=100, category=None):
    if category:
        return _execute("SELECT * FROM logs WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                        (category, limit), "all")
    return _execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,), "all")

def add_user(user_id, username, is_admin=0):
    _execute('''
        INSERT INTO users (user_id, username, is_admin)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            is_admin=CASE WHEN users.is_admin = 1 THEN 1 ELSE excluded.is_admin END
    ''', (user_id, username, is_admin))

def get_user(user_id):
    return _execute("SELECT * FROM users WHERE user_id = ?", (user_id,), "one")

def get_user_balance(user_id) -> float:
    row = _execute("SELECT balance FROM users WHERE user_id = ?", (user_id,), "one")
    return float(row["balance"]) if row else 0.0

def credit_wallet(user_id, amount, description) -> float:
    _execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    _execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (?, 'credit', ?, ?)",
             (user_id, amount, description))
    return get_user_balance(user_id)

def debit_wallet(user_id, amount, description) -> float:
    _execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    _execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (?, 'debit', ?, ?)",
             (user_id, -amount, description))
    return get_user_balance(user_id)

def get_user_transactions(user_id):
    return _execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50", (user_id,), "all")

def get_all_transactions():
    return _execute("SELECT t.*, u.username FROM transactions t LEFT JOIN users u ON t.user_id = u.user_id ORDER BY t.timestamp DESC LIMIT 100", (), "all")

def create_recharge_request(user_id, amount) -> int:
    return _execute("INSERT INTO recharge_requests (user_id, amount, status) VALUES (?, ?, 'pending')", (user_id, amount))

def get_recharge_request(request_id):
    return _execute("SELECT r.*, u.username FROM recharge_requests r JOIN users u ON r.user_id = u.user_id WHERE r.id = ?", (request_id,), "one")

def update_recharge_request(request_id, status):
    _execute("UPDATE recharge_requests SET status = ? WHERE id = ?", (status, request_id))

def get_pending_recharge_requests():
    return _execute("SELECT r.*, u.username FROM recharge_requests r JOIN users u ON r.user_id = u.user_id WHERE r.status = 'pending' ORDER BY r.timestamp DESC", (), "all")

def get_admin_settings():
    rows = _execute("SELECT * FROM admin_settings", (), "all")
    return {r["key"]: r["value"] for r in rows}

def update_admin_setting(key, value):
    _execute("INSERT INTO admin_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

def is_admin(user_id) -> bool:
    row = _execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,), "one")
    return bool(row["is_admin"]) if row else False

def add_service(service_id, country, service_name, service_price, is_enabled=1, is_top=0):
    _execute('''
        INSERT INTO services (service_id, country, service_name, service_price, is_enabled, is_top)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(service_id, country) DO UPDATE SET
            service_name=excluded.service_name,
            service_price=excluded.service_price,
            is_enabled=excluded.is_enabled,
            is_top=excluded.is_top
    ''', (service_id, country, service_name, service_price, is_enabled, is_top))

def edit_service_price(service_id, country, price):
    _execute("UPDATE services SET service_price = ? WHERE service_id = ? AND country = ?", (price, service_id, country))

def delete_service(service_id, country):
    _execute("DELETE FROM services WHERE service_id = ? AND country = ?", (service_id, country))

def toggle_service_enabled(service_id, country, is_enabled):
    _execute("UPDATE services SET is_enabled = ? WHERE service_id = ? AND country = ?", (is_enabled, service_id, country))

def toggle_service_top(service_id, country, is_top):
    _execute("UPDATE services SET is_top = ? WHERE service_id = ? AND country = ?", (is_top, service_id, country))

def get_services(country) -> dict:
    rows = _execute("SELECT * FROM services WHERE country = ?", (country,), "all")
    return {r["service_id"]: {
        "service_name": r["service_name"],
        "service_price": r["service_price"],
        "is_enabled": r["is_enabled"],
        "is_top": r["is_top"]
    } for r in rows}

def get_top_services(country) -> list:
    return _execute("SELECT * FROM services WHERE country = ? AND is_top = 1 AND is_enabled = 1 ORDER BY service_name ASC", (country,), "all")

def get_all_services_list():
    return _execute("SELECT * FROM services ORDER BY is_top DESC, country ASC, service_name ASC", (), "all")

def get_all_top_services():
    return _execute("SELECT * FROM services WHERE is_top = 1 ORDER BY country ASC, service_name ASC", (), "all")

def get_all_users():
    return _execute("SELECT * FROM users ORDER BY username ASC", (), "all")