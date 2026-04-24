import os
import pandas as pd
from dotenv import load_dotenv
from edgar import set_identity, Company
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# 1. LOAD CONFIGURATION
load_dotenv()
SEC_ID = os.getenv("SEC_IDENTITY")
set_identity(SEC_ID)

# 2. SECURE DATABASE CONNECTION
# This uses the "Split Method" we discussed to handle special characters safely
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

# 3. THE REVENUE LOGIC
REVENUE_TAGS = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet", "RevenueFromContractWithCustomerExcludingAssessedTax"]

def sync_revenue(ticker):
    print(f"🚀 Processing {ticker}...")
    company = Company(ticker)
    facts = company.get_facts().to_pandas()
    
    # Filter for revenue tags
    df = facts[facts['fact'].isin(REVENUE_TAGS)].copy()
    if df.empty:
        print(f"⚠️ No revenue data found for {ticker}")
        return

    # Clean and Calculate Growth
    df = df[df['form'].isin(['10-K', '10-Q'])]
    df = df[['end', 'val', 'fact', 'fp', 'fy']].drop_duplicates(subset=['end'])
    df['end'] = pd.to_datetime(df['end'])
    df = df.sort_values('end')
    
    # Year-over-Year Growth
    df['revenue_yoy_growth'] = df['val'].pct_change(periods=4) * 100
    df['ticker'] = ticker

    # SAVE TO POSTGRES
    df.to_sql("revenue_tracker", engine, if_exists='append', index=False)
    print(f"✅ {ticker} synced to database.")

# 4. RUN IT
if __name__ == "__main__":
    watchlist = ["NVDA", "TSLA", "MSFT", "AAPL"]
    
    # Clear old data for a fresh start (Optional)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_tracker;"))
        conn.commit()

    for stock in watchlist:
        try:
            sync_revenue(stock)
        except Exception as e:
            print(f"❌ Error with {stock}: {e}")

    print("\n--- ALL DONE! Check pgAdmin for your data. ---")

    # Add this to the bottom of your 'if __name__ == "__main__":' block
    with engine.connect() as conn:
        result = pd.read_sql("SELECT ticker, end, val, revenue_yoy_growth FROM revenue_tracker WHERE revenue_yoy_growth IS NOT NULL LIMIT 5", conn)
        print("\n--- DATABASE PREVIEW ---")
        print(result)
