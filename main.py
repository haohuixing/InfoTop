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

# 3. THE REVENUE LOGIC
REVENUE_TAGS = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet", "RevenueFromContractWithCustomerExcludingAssessedTax"]

def sync_revenue(ticker):
    print(f"🚀 Processing {ticker}...")
    company = Company(ticker)
    
    # FIX: Robust facts extraction
    facts_obj = company.get_facts()
    # If to_pandas() is missing, we use the facts object directly in a DataFrame
    try:
        df = facts_obj.to_pandas()
    except AttributeError:
        df = pd.DataFrame(facts_obj)

    if df is None or df.empty:
        print(f"⚠️ No revenue data found for {ticker}")
        return

    # Clean and Calculate Growth
    df = df[df['form'].isin(['10-K', '10-Q'])].copy()
    
    # Filter for our revenue tags
    df = df[df['fact'].isin(REVENUE_TAGS)]
    
    if df.empty:
        print(f"⚠️ No matching revenue tags for {ticker}")
        return

    df = df[['end', 'val', 'fact', 'fp', 'fy']].drop_duplicates(subset=['end'])
    df['end'] = pd.to_datetime(df['end'])
    df = df.sort_values('end')
    
    # Year-over-Year Growth (shift by 4 quarters)
    df['revenue_yoy_growth'] = df['val'].pct_change(periods=4) * 100
    df['ticker'] = ticker

    # SAVE TO POSTGRES
    # We rename 'end' to 'period_end' to avoid Postgres reserved word issues in the future
    df = df.rename(columns={'end': 'period_end'})
    df.to_sql("revenue_tracker", engine, if_exists='append', index=False)
    print(f"✅ {ticker} synced to database.")

# 4. RUN IT
if __name__ == "__main__":
    watchlist = ["NVDA", "TSLA", "MSFT", "AAPL"]
    
    # Fresh start
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_tracker;"))
        conn.commit()

    for stock in watchlist:
        try:
            sync_revenue(stock)
        except Exception as e:
            print(f"❌ Error with {stock}: {e}")

    print("\n--- ALL DONE! Check pgAdmin for your data. ---")

    # 5. PREVIEW DATA
    # FIX: We use "period_end" now because we renamed it above
    try:
        with engine.connect() as conn:
            query = text("SELECT ticker, period_end, val, revenue_yoy_growth FROM revenue_tracker WHERE revenue_yoy_growth IS NOT NULL LIMIT 5")
            result = pd.read_sql(query, conn)
            print("\n--- DATABASE PREVIEW ---")
            print(result)
    except Exception as e:
        print(f"Could not preview data: {e}")
