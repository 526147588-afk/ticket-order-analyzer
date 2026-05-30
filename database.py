import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """初始化数据库"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_date TEXT NOT NULL,
            file_name TEXT,
            order_count INTEGER,
            total_profit REAL,
            total_amount REAL,
            data_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_data(df, file_name=None):
    """保存数据到历史记录"""
    conn = get_connection()
    upload_date = datetime.now().strftime('%Y-%m-%d')
    order_count = len(df)
    total_profit = pd.to_numeric(df['利润'], errors='coerce').sum()
    total_amount = pd.to_numeric(df['支付金额'], errors='coerce').sum()
    data_json = df.to_json(orient='records', force_ascii=False)

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (upload_date, file_name, order_count, total_profit, total_amount, data_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (upload_date, file_name, order_count, total_profit, total_amount, data_json))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def get_all_history():
    """获取所有历史记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, upload_date, file_name, order_count, total_profit, total_amount, created_at
        FROM history ORDER BY created_at DESC
    ''')
    records = cursor.fetchall()
    conn.close()
    return records

def get_history_data(record_id):
    """获取指定历史记录的数据"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT data_json FROM history WHERE id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        df = pd.read_json(row[0], orient='records')
        return df
    return None

def get_multi_history_data(record_ids):
    """获取多个历史记录的数据并合并"""
    if not record_ids:
        return None
    dfs = []
    for rid in record_ids:
        df = get_history_data(rid)
        if df is not None:
            dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return None

def delete_history(record_id):
    """删除历史记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

# 初始化数据库
init_db()