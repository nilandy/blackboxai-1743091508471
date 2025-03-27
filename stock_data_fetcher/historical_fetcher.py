import yfinance as yf
from .db import get_db_connection, update_stock_timestamp
from datetime import datetime, timedelta
import logging
import time
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Interval configuration
INTERVAL_CONFIG = {
    '1m': {'max_days': 7, 'chunk_days': 6},
    '2m': {'max_days': 60, 'chunk_days': 30},
    '5m': {'max_days': 60, 'chunk_days': 30},
    '15m': {'max_days': 60, 'chunk_days': 30},
    '30m': {'max_days': 60, 'chunk_days': 30},
    '60m': {'max_days': 60, 'chunk_days': 30},
    '90m': {'max_days': 60, 'chunk_days': 30},
    '1h': {'max_days': 60, 'chunk_days': 30},
    '1d': {'max_days': None, 'chunk_days': None},
    '5d': {'max_days': None, 'chunk_days': None},
    '1wk': {'max_days': None, 'chunk_days': None},
    '1mo': {'max_days': None, 'chunk_days': None},
    '3mo': {'max_days': None, 'chunk_days': None}
}

def fetch_historical_data(symbol, interval):
    """Fetch historical data for a stock at given interval"""
    if interval not in INTERVAL_CONFIG:
        raise ValueError(f"Unsupported interval: {interval}")
    
    config = INTERVAL_CONFIG[interval]
    ticker = yf.Ticker(f"{symbol}.NS")
    
    if config['max_days']:
        # Fetch in chunks for intervals with limits
        end_date = datetime.now()
        start_date = _get_earliest_date(symbol, interval) or datetime.now() - timedelta(days=config['max_days'])
        
        while start_date < end_date:
            chunk_end = min(start_date + timedelta(days=config['chunk_days']), end_date)
            logger.info(f"Fetching {symbol} {interval} data from {start_date} to {chunk_end}")
            
            data = ticker.history(
                start=start_date,
                end=chunk_end,
                interval=interval,
                actions=False
            )
            
            if not data.empty:
                _store_data(symbol, interval, data)
            
            start_date = chunk_end
            time.sleep(1)  # Rate limiting
    else:
        # No limits, fetch all at once
        logger.info(f"Fetching all {interval} data for {symbol}")
        data = ticker.history(period="max", interval=interval, actions=False)
        if not data.empty:
            _store_data(symbol, interval, data)
    
    update_stock_timestamp(symbol)

def _get_earliest_date(symbol, interval):
    """Get the earliest date we have data for this symbol/interval"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT MAX(datetime) FROM stock_data 
                WHERE symbol = ? AND interval = ?''',
             (symbol, interval))
    result = c.fetchone()
    conn.close()
    return datetime.fromisoformat(result[0]) if result[0] else None

def _store_data(symbol, interval, data):
    """Store fetched data in database"""
    conn = get_db_connection()
    c = conn.cursor()
    
    for index, row in data.iterrows():
        c.execute('''INSERT OR IGNORE INTO stock_data
                    (symbol, interval, datetime, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (symbol, interval, index.isoformat(), 
                  row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
    
    conn.commit()
    conn.close()
    logger.info(f"Stored {len(data)} records for {symbol} {interval}")

def fetch_all_intervals(symbol):
    """Fetch data for all intervals for a stock"""
    for interval in INTERVAL_CONFIG:
        try:
            fetch_historical_data(symbol, interval)
        except Exception as e:
            logger.error(f"Error fetching {interval} data for {symbol}: {str(e)}")