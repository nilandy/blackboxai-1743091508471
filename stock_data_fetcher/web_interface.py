from flask import Flask, render_template, request, send_file, jsonify
from .db import get_db_connection
from .nse_fetcher import get_all_stock_symbols
from .historical_fetcher import fetch_all_intervals
import pandas as pd
from io import BytesIO
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    c = conn.cursor()
    
    if search_query:
        c.execute('''SELECT symbol, name, last_updated FROM stocks 
                    WHERE symbol LIKE ? OR name LIKE ?
                    ORDER BY symbol''',
                 (f'%{search_query}%', f'%{search_query}%'))
    else:
        c.execute('SELECT symbol, name, last_updated FROM stocks ORDER BY symbol')
    
    stocks = [{
        'symbol': row[0],
        'name': row[1],
        'last_updated': row[2]
    } for row in c.fetchall()]
    
    conn.close()
    return render_template('index.html', stocks=stocks, search_query=search_query)

@app.route('/fetch/<symbol>')
def fetch_stock_data(symbol):
    try:
        fetch_all_intervals(symbol)
        return jsonify({'status': 'success', 'message': f'Data fetched for {symbol}'})
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/export')
def export_data():
    try:
        conn = get_db_connection()
        
        # Get all stock data
        df = pd.read_sql('''
            SELECT s.symbol, s.name, d.interval, d.datetime, 
                   d.open, d.high, d.low, d.close, d.volume
            FROM stock_data d
            JOIN stocks s ON d.symbol = s.symbol
            ORDER BY s.symbol, d.interval, d.datetime
        ''', conn)
        
        conn.close()
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='stock_data_export.csv'
        )
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)