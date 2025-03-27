from nsetools import Nse
from .db import get_db_connection, update_stock_timestamp
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all_stocks():
    """Fetch all stocks from NSE and store in database"""
    nse = Nse()
    try:
        all_stocks = nse.get_stock_codes()
        if not all_stocks:
            raise ValueError("No stocks returned from NSE")
            
        # Remove header if exists
        if 'SYMBOL' in all_stocks:
            del all_stocks['SYMBOL']
            
        conn = get_db_connection()
        c = conn.cursor()
        
        for symbol, name in all_stocks.items():
            # Check if stock exists
            c.execute('SELECT 1 FROM stocks WHERE symbol = ?', (symbol,))
            exists = c.fetchone()
            
            if exists:
                logger.debug(f"Stock {symbol} already exists, skipping")
            else:
                c.execute('''INSERT INTO stocks 
                          (symbol, name, last_updated) 
                          VALUES (?, ?, ?)''',
                       (symbol, name, datetime.now().isoformat()))
                logger.info(f"Added new stock: {symbol} - {name}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error fetching stocks: {str(e)}")
        return False

def get_all_stock_symbols():
    """Get list of all stock symbols from database"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT symbol FROM stocks ORDER BY symbol')
    symbols = [row[0] for row in c.fetchall()]
    conn.close()
    return symbols