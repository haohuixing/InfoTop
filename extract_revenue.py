import os
import pandas as pd
from dotenv import load_dotenv
from edgar import set_identity, Company
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# 1. SETUP
load_dotenv()
set_identity(os.getenv("SEC_IDENTITY"))

# Database connection using the secure "Split Method"
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

def sync_revenue_growth(ticker):
    print(f"🚀 Analyzing {ticker}...")
    company = Company(ticker)
    
    # 2. GET HIGH-LEVEL INCOME STATEMENT
    # periods=2 gives us Current Year vs Prior Year automatically
    stmt = company.income_statement(periods=2)
    if not stmt:
        print(f"⚠️ Could not generate income statement for {ticker}")
        return

    # 3. CONVERT TO DATAFRAME
    df = stmt.to_dataframe()
    if df.empty:
        print(f"⚠️ Dataframe is empty for {ticker}")
        return

    # 4. LOCATE THE REVENUE ROW
    # We look for rows labeled 'Revenue' or 'Net Sales'
    revenue_row_mask = df['label'].str.contains('Revenue|Net Sales|Total net sales', case=False, na=False)
    if not revenue_row_mask.any():
        print(f"⚠️ Could not find Revenue label in statement. Rows: {df['label'].tolist()}")
        return
    
    revenue_row = df[revenue_row_mask].iloc[0]

    # 5. EXTRACT PERIODS & VALUES
    # stmt.periods contains the column headers (e.g., 'FY 2024', 'FY 2023')
    periods = stmt.periods
    if len(periods) < 2:
        print(f"⚠️ Not enough periods for growth calculation for {ticker}")
        return

    current_period = periods[0]
    prior_period = periods[1]

    current_val = revenue_row[current_period]
    prior_val = revenue_row[prior_period]

    if pd.isna(current_val) or pd.isna(prior_val) or prior_val == 0:
        print(f"⚠️ Invalid data values for {ticker}")
        return

    # 6. CALCULATE GROWTH
    growth = ((current_val - prior_val) / prior_val) * 100

    # 7. PREP DATA FOR POSTGRES
    # We create a clean, single-row dataframe for this ticker's latest update
    db_data = pd.DataFrame([{
        'ticker': ticker,
        'current_period': current_period,
        'prior_period': prior_period,
        'revenue_current': current_val,
        'revenue_prior': prior_val,
        'growth_pct': round(growth, 2)
    }])

    # 8. SAVE TO DB
    db_data.to_sql("revenue_growth_tracker", engine, if_exists='append', index=False)
    print(f"✅ {ticker} Synced: {growth:.1f}% growth ({current_period} vs {prior_period})")

if __name__ == "__main__":
    # Clear the table for a fresh start
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_growth_tracker;"))
        conn.commit()
        print("🧹 Database cleaned.")

    watchlist = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL']
    
    for ticker in watchlist:
        try:
            sync_revenue_growth(ticker)
        except Exception as e:
            print(f"❌ Error with {ticker}: {e}")

    print("\n--- SYNC COMPLETE ---")

    # 9. FINAL DASHBOARD PREVIEW
    try:
        with engine.connect() as conn:
            res = pd.read_sql("SELECT * FROM revenue_growth_tracker ORDER BY growth_pct DESC", conn)
            print("\n--- REVENUE GROWTH DASHBOARD (PostgreSQL) ---")
            # Formatting for the terminal
            res['revenue_current'] = res['revenue_current'].apply(lambda x: f"${x:,.0f}")
            res['growth_pct'] = res['growth_pct'].apply(lambda x: f"{x}%")
            print(res)
    except Exception as e:
        print(f"Nothing to display: {e}")