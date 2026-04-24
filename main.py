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

# 2. SECURE DATABASE CONNECTION
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

# 3. REVENUE TAGS (SEC uses these for "Top Line" Revenue)
REVENUE_TAGS = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet", "RevenueFromContractWithCustomerExcludingAssessedTax"]

def sync_revenue(ticker):
    print(f"🚀 Processing {ticker}...")
    company = Company(ticker)
    
    # NEW: The most robust way to get facts in the latest edgartools
    facts = company.get_facts()
    
    # Convert facts to a DataFrame. Some versions use .to_pandas(), others .to_dataframe()
    # We use a helper to find the right one.
    if hasattr(facts, 'to_pandas'):
        df = facts.to_pandas()
    elif hasattr(facts, 'to_dataframe'):
        df = facts.to_dataframe()
    else:
        # Fallback for very new versions that require a query first
        df = facts.query().to_pandas()

    if df is None or df.empty:
        print(f"⚠️ No facts found for {ticker}")
        return

    # LOGIC FIX: Some SEC facts don't include 'form' directly in the table. 
    # We will filter by common timeframes instead (Quarterly/Annual)
    # We want to make sure we have columns: 'fact', 'val', 'end', and 'fp'
    
    # Ensure column names are standardized (case-insensitive check)
    df.columns = [c.lower() for c in df.columns]
    
    # Target columns (handling variations in naming like 'value' vs 'val')
    col_map = {'value': 'val', 'date': 'end', 'period_end': 'end'}
    df = df.rename(columns=col_map)

    # Filter for Revenue Tags
    df = df[df['fact'].isin(REVENUE_TAGS)].copy()
    
    if df.empty:
        print(f"⚠️ No revenue tags found for {ticker}")
        return

    # Drop duplicates to keep the "cleanest" timeline
    df = df.drop_duplicates(subset=['end'])
    df['end'] = pd.to_datetime(df['end'])
    df = df.sort_values('end')
    
    # Calculate Year-over-Year Growth (comparing same quarter last year)
    df['revenue_yoy_growth'] = df['val'].pct_change(periods=4) * 100
    df['ticker'] = ticker

    # Rename 'end' to 'period_end' to avoid Postgres SQL keywords
    df = df.rename(columns={'end': 'period_end'})

    # SAVE TO POSTGRES
    # We only save the columns we care about
    final_cols = ['ticker', 'period_end', 'val', 'fact', 'revenue_yoy_growth']
    existing_cols = [c for c in final_cols if c in df.columns]
    
    df[existing_cols].to_sql("revenue_tracker", engine, if_exists='append', index=False)
    print(f"✅ {ticker} synced to database.")

if __name__ == "__main__":
    watchlist = ["NVDA", "TSLA", "MSFT", "AAPL"]
    
    # Wipe the table to start fresh so we don't get duplicates during testing
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_tracker;"))
        conn.commit()

    for stock in watchlist:
        try:
            sync_revenue(stock)
        except Exception as e:
            print(f"❌ Error with {stock}: {e}")

    print("\n--- ALL DONE! ---")

    # PREVIEW
    try:
        with engine.connect() as conn:
            query = text("SELECT ticker, period_end, val, revenue_yoy_growth FROM revenue_tracker WHERE revenue_yoy_growth IS NOT NULL LIMIT 10")
            result = pd.read_sql(query, conn)
            print("\n--- DATABASE PREVIEW ---")
            print(result)
    except Exception as e:
        print(f"Could not preview data (Table might be empty): {e}")
