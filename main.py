import pandas as pd
from sqlalchemy import text
from extraction_scripts.extract_revenue import sync_revenue_growth, engine
from process import run_analysis, format_to_markdown

# Import the new distribution modules
from web_generator import create_site_dashboard
from email_dispatcher import dispatch_to_subscribers

def main():
    # --- PHASE 1: GATHER (EXTRACTION) ---
    print("--- PHASE 1: EXTRACTION ---")
    watchlist = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL']
    
    # Optional: Clear table for a fresh run so we don't have duplicate data
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_growth_tracker;"))
        conn.commit()
        print("🧹 Database cleaned for fresh run.")

    for ticker in watchlist:
        try:
            sync_revenue_growth(ticker)
        except Exception as e:
            print(f"❌ Error extracting {ticker}: {e}")

    # --- PHASE 2: PROCESS (ANALYSIS) ---
    print("\n--- PHASE 2: PROCESSING & ANALYSIS ---")
    # Pull the fresh data back from the DB
    df = pd.read_sql("SELECT * FROM revenue_growth_tracker", engine)
    
    # Run our logic to get sentiment and summaries
    analyzed_list = run_analysis(df)
    
    # Create the text-based markdown for a local backup
    report_md = format_to_markdown(analyzed_list)

    # --- PHASE 3: OUTPUT & DISTRIBUTION ---
    print("\n--- PHASE 3: OUTPUT & DISTRIBUTION ---")
    
    # 1. Save local Markdown backup
    with open("latest_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)
        print("📝 Local Markdown report saved.")

    # 2. Generate the Website (index.html)
    try:
        create_site_dashboard(analyzed_list)
    except Exception as e:
        print(f"❌ Web Generation Error: {e}")

    # 3. Dispatch Emails to Subscribers
    # Note: Ensure your RESEND_API_KEY is in your .env file!
    try:
        dispatch_to_subscribers(analyzed_list)
    except Exception as e:
        print(f"❌ Email Dispatch Error: {e}")

    print("\n✅ MISSION COMPLETE: Data synced, site updated, and emails sent.")

if __name__ == "__main__":
    main()
