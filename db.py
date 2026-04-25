import sqlite3
import datetime
import calendar
import os
import csv

DB_NAME = "finance.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            monthly_budget REAL DEFAULT 0.0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            category TEXT,
            amount REAL,
            timestamp DATETIME,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

def set_budget(user_id: int, amount: float):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO users (user_id, monthly_budget) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET monthly_budget=excluded.monthly_budget', (user_id, amount))
    conn.commit()
    conn.close()

def get_budget(user_id: int) -> float:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT monthly_budget FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row['monthly_budget'] if row else 0.0

def add_transaction(user_id: int, trans_type: str, category: str, amount: float, description: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    
    timestamp = datetime.datetime.now()
    c.execute('''
        INSERT INTO transactions (user_id, type, category, amount, timestamp, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, trans_type, category, amount, timestamp, description))
    conn.commit()
    conn.close()
    
    try:
        file_exists = os.path.isfile("finance_logs.csv")
        with open("finance_logs.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "User ID", "Type", "Category", "Amount", "Description"])
            writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), user_id, trans_type, category, amount, description])
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def get_current_month_spending(user_id: int) -> float:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    c.execute('''
        SELECT SUM(amount) as total FROM transactions
        WHERE user_id = ? AND type = 'expense' AND timestamp >= ?
    ''', (user_id, start_of_month))
    row = c.fetchone()
    conn.close()
    return row['total'] if row and row['total'] else 0.0

def get_current_month_spending_by_category(user_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    c.execute('''
        SELECT category, SUM(amount) as total FROM transactions
        WHERE user_id = ? AND type = 'expense' AND timestamp >= ?
        GROUP BY category
    ''', (user_id, start_of_month))
    rows = c.fetchall()
    conn.close()
    return {row['category']: row['total'] for row in rows}

def get_financial_context(user_id: int) -> dict:
    budget = get_budget(user_id)
    spent = get_current_month_spending(user_id)
    spent_by_category = get_current_month_spending_by_category(user_id)
    now = datetime.datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    
    return {
        "monthly_budget": budget,
        "total_spent_this_month": spent,
        "remaining_budget": budget - spent,
        "spent_by_category": spent_by_category,
        "day_of_month": now.day,
        "days_in_month": days_in_month
    }

def get_all_transactions(user_id: int) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 100', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
