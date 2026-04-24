import os
import pandas as pd
from dotenv import load_dotenv
from edgar import set_identity, Company
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# 1. LOAD CONFIGURATION
load_dotenv()
SEC_ID = os.getenv("SEC_IDENTITY")
if not SEC_ID:
    print("❌ SEC_IDENTITY not found in .env")
    exit()
set_identity(SEC_ID)

# 2. DATABASE CONNECTION
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

# The most common SEC tags for Revenue
REVENUE_TAGS = ["Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueGoodsNet"]

def sync_revenue(ticker):
    print(f"🚀 Processing {ticker}...")
    company = Company(ticker)
    
    # Get all facts for the company
    facts = company.get_facts()
    
    # We will try to find a match from our REVENUE_TAGS list
    revenue_df = None
    found_tag = None

    for tag in REVENUE_TAGS:
        try:
            # This is the most reliable way to get a specific concept
            data = facts.get_concept('us-gaap', tag)
            if data is not None:
                df = data.to_pandas()
                if not df.empty:
                    revenue_df = df
                    found_tag = tag
                    break # Stop once we find a valid revenue tag
        except:
            continue

    if revenue_df is None:
        print(f"⚠️ No revenue tags found for {ticker}")
        return

    # Standardize column names (Edgar can return 'val' or 'value', 'end' or 'date')
    revenue_df.columns = [c.lower() for c in revenue_df.columns]
    col_map = {'value': 'val', 'date': 'end'}
    revenue_df = revenue_df.rename(columns=col_map)

    # Filter for standard filings (10-K, 10-Q) if the column exists
    if 'form' in revenue_df.columns:
        revenue_df = revenue_df[revenue_df['form'].isin(['10-K', '10-Q'])].copy()

    # Drop duplicates on the end date
    revenue_df = revenue_df.drop_duplicates(subset=['end'])
    revenue_df['end'] = pd.to_datetime(revenue_df['end'])
    revenue_df = revenue_df.sort_values('end')

    # Calculate Growth (comparing to same quarter/period 1 year ago)
    # Note: Using periods=4 for quarterly data
    revenue_df['revenue_yoy_growth'] = revenue_df['val'].pct_change(periods=4) * 100
    revenue_df['ticker'] = ticker
    revenue_df['fact_used'] = found_tag

    # Rename 'end' to 'period_end' for Postgres safety
    revenue_df = revenue_df.rename(columns={'end': 'period_end'})

    # SAVE TO POSTGRES
    # Select only relevant columns to avoid 'extra column' errors
    cols_to_save = ['ticker', 'period_end', 'val', 'revenue_yoy_growth', 'fact_used']
    revenue_df[cols_to_save].to_sql("revenue_tracker", engine, if_exists='append', index=False)
    
    print(f"✅ {ticker} synced using tag: {found_tag}")

if __name__ == "__main__":
    watchlist = ["NVDA", "TSLA", "MSFT", "AAPL"]
    
    # Fresh start: Drop the table if it exists
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_tracker;"))
        conn.commit()
        print("🧹 Database cleaned. Starting fresh...")

    for stock in watchlist:
        try:
            sync_revenue(stock)
        except Exception as e:
            print(f"❌ Critical Error with {stock}: {e}")

    print("\n--- SYNC COMPLETE ---")

    # PREVIEW
    try:
        with engine.connect() as conn:
            query = text("SELECT ticker, period_end, val, revenue_yoy_growth FROM revenue_tracker WHERE revenue_yoy_growth IS NOT NULL ORDER BY period_end DESC LIMIT 10")
            result = pd.read_sql(query, conn)
            print("\n--- LATEST REVENUE GROWTH DATA ---")
            print(result)
    except Exception as e:
        print(f"No data to preview: {e}")
