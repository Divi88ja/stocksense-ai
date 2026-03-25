"""
Ingestion Agent
Fetches OHLCV price data and SEBI filings, normalizes, and stores them.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger


NSE_500_SAMPLE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "TATAMOTORS.NS", "WIPRO.NS", "ADANIENT.NS", "AXISBANK.NS", "MARUTI.NS",
]


def fetch_ohlcv(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Fetch OHLCV data for a given NSE symbol."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        df["symbol"] = symbol
        df.reset_index(inplace=True)
        logger.info(f"Fetched {len(df)} rows for {symbol}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch {symbol}: {e}")
        return pd.DataFrame()


def fetch_bulk_deals() -> pd.DataFrame:
    """
    Fetch bulk/block deal data from NSE.
    In production: scrape https://www.nseindia.com/market-data/bulk-deals
    For demo: returns sample data.
    """
    sample_data = [
        {
            "date": datetime.today().strftime("%Y-%m-%d"),
            "symbol": "TATAMOTORS",
            "client_name": "TATA SONS PRIVATE LIMITED",
            "deal_type": "BUY",
            "quantity": 5000000,
            "price": 950.5,
            "value_cr": 47.5,
            "category": "PROMOTER"
        },
        {
            "date": datetime.today().strftime("%Y-%m-%d"),
            "symbol": "HDFCBANK",
            "client_name": "GOVERNMENT OF SINGAPORE",
            "deal_type": "BUY",
            "quantity": 2000000,
            "price": 1520.0,
            "value_cr": 30.4,
            "category": "FII"
        }
    ]
    return pd.DataFrame(sample_data)


def fetch_insider_trades() -> pd.DataFrame:
    """
    Fetch insider trading data from SEBI disclosures.
    In production: parse SEBI SAST / PIT regulation filings.
    For demo: returns sample data.
    """
    sample_data = [
        {
            "date": (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "symbol": "TATAMOTORS",
            "person_name": "N. Chandrasekaran",
            "designation": "Chairman",
            "transaction_type": "BUY",
            "shares": 100000,
            "price": 948.0,
            "value_cr": 9.48,
            "consecutive_buys": 3
        }
    ]
    return pd.DataFrame(sample_data)


def run_ingestion():
    """Main ingestion pipeline."""
    logger.info("Starting ingestion run...")

    all_prices = []
    for symbol in NSE_500_SAMPLE:
        df = fetch_ohlcv(symbol, period="1y")
        if not df.empty:
            all_prices.append(df)

    if all_prices:
        prices_df = pd.concat(all_prices, ignore_index=True)
        prices_df.to_csv("data/processed/prices.csv", index=False)
        logger.info(f"Saved {len(prices_df)} price rows to data/processed/prices.csv")

    bulk_deals = fetch_bulk_deals()
    bulk_deals.to_csv("data/processed/bulk_deals.csv", index=False)
    logger.info(f"Saved {len(bulk_deals)} bulk deal rows")

    insider_trades = fetch_insider_trades()
    insider_trades.to_csv("data/processed/insider_trades.csv", index=False)
    logger.info(f"Saved {len(insider_trades)} insider trade rows")

    logger.info("Ingestion run complete.")


if __name__ == "__main__":
    run_ingestion()
