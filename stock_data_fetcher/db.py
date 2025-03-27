import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('stocks.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS stocks
                 (symbol text PRIMARY KEY, name text, isin text, 
                  last_updated text)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS stock_data
                 (id integer PRIMARY KEY AUTOINCREMENT,
                  symbol text, 
                  interval text,
                  datetime text,
                  open real,
                  high real,
                  low real,
                  close real,
                  volume integer,
                  FOREIGN KEY (symbol) REFERENCES stocks (symbol))''')
    
    # Create index for faster searches
    c.execute('''CREATE INDEX IF NOT EXISTS idx_stock_data 
                 ON stock_data(symbol, interval, datetime)''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect('stocks.db')

def update_stock_timestamp(symbol):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''UPDATE stocks 
                SET last_updated = ?
                WHERE symbol = ?''',
             (datetime.now().isoformat(), symbol))
    conn.commit()
    conn.close()