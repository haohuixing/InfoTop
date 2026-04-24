import pandas as pd
from edgar import set_identity, Company
from sqlalchemy import create_engine, text
import numpy as np

# --- CONFIGURATION ---
set_identity("Your Name your.email@example.com")
DATABASE_URL = "postgresql://postgres:password@localhost:5432/edgar_db"
engine = create_engine(DATABASE_URL)

# Common XBRL tags for Revenue (Companies use different ones)
REVENUE_TAGS = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet", "RevenueFromContractWithCustomerExcludingAssessedTax"]

def get_historical_revenue(ticker):
    print(f"Fetching revenue data for {ticker}...")
    company = Company(ticker)
    
    # get_facts() returns a huge table of every reported metric
    facts = company.get_facts().to_pandas()
    
    # Filter for the best available revenue concept
    revenue_data = facts[facts['fact'].isin(REVENUE_TAGS)].copy()
    
    if revenue_data.empty:
        print(f"No standard revenue tags found for {ticker}")
        return None

    # Standardize: We want 'end' date, 'val' (value), and the 'fact' tag used
    # We filter for 'form' in ['10-K', '10-Q'] to avoid duplicates in other filings
    revenue_data = revenue_data[revenue_data['form'].isin(['10-K', '10-Q'])]
    
    # Select key columns and drop duplicates (SEC often repeats values in different frames)
    df = revenue_data[['end', 'val', 'fact', 'fp', 'fy']].drop_duplicates(subset=['end'])
    df['end'] = pd.to_datetime(df['end'])
    df = df.sort_values('end')

    # Calculate Growth (%)
    # Since we have both 10-Q (Quarterly) and 10-K (Annual), 
    # we shift by 4 periods to get Year-over-Year (YoY) for that specific quarter
    df['revenue_yoy_growth'] = df['val'].pct_change(periods=4) * 100
    df['ticker'] = ticker
    
    return df

def sync_to_db(tickers):
    for ticker in tickers:
        try:
            df = get_historical_revenue(ticker)
            if df is not None:
                # Save to a dedicated 'revenue_tracker' table
                df.to_sql("revenue_tracker", engine, if_exists='append', index=False)
                print(f"✅ Synced {ticker} to Database.")
        except Exception as e:
            print(f"❌ Error syncing {ticker}: {e}")

def run_simple_dashboard():
    """Prints a quick growth report from the database."""
    query = """
        SELECT ticker, end as date, val/1000000 as rev_millions, revenue_yoy_growth 
        FROM revenue_tracker 
        WHERE revenue_yoy_growth IS NOT NULL
        ORDER BY end DESC LIMIT 10;
    """
    with engine.connect() as conn:
        result = pd.read_sql(query, conn)
        print("\n--- REVENUE GROWTH DASHBOARD ---")
        print(result)

if __name__ == "__main__":
    # 1. Choose your watchlist
    watchlist = ["NVDA", "PLTR", "COIN", "TSLA", "MSFT"]
    
    # 2. Sync data
    sync_to_db(watchlist)
    
    # 3. View the results
    run_simple_dashboard()