from stock_data_fetcher.db import init_db
from stock_data_fetcher.nse_fetcher import fetch_all_stocks
from stock_data_fetcher.web_interface import app
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='NSE Stock Data Fetcher')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--fetch-symbols', action='store_true', 
                       help='Fetch all stock symbols from NSE')
    parser.add_argument('--run', action='store_true', 
                       help='Run the web interface')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the web interface on')
    
    args = parser.parse_args()

    if args.init:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")

    if args.fetch_symbols:
        logger.info("Fetching stock symbols from NSE...")
        if fetch_all_stocks():
            logger.info("Successfully fetched stock symbols")
        else:
            logger.error("Failed to fetch stock symbols")

    if args.run:
        logger.info(f"Starting web interface on port {args.port}")
        app.run(host='0.0.0.0', port=args.port, debug=True)

if __name__ == '__main__':
    main()