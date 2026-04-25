import pandas as pd
from extraction_scripts.extract_revenue import sync_revenue_growth, engine
from process import run_analysis, format_to_markdown
from sqlalchemy import text

# IMPORT YOUR NEW MODULES
from web_generator import create_site_dashboard
from email_dispatcher import dispatch_to_subscribers

def main():
    # --- PHASE 1: EXTRACTION ---
    watchlist = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL']
    for ticker in watchlist:
        sync_revenue_growth(ticker)

    # --- PHASE 2: PROCESSING ---
    df = pd.read_sql("SELECT * FROM revenue_growth_tracker", engine)
    analyzed_list = run_analysis(df)
    report_md = format_to_markdown(analyzed_list)

    # --- PHASE 3: DISTRIBUTION ---
    print("\n--- PHASE 3: DISTRIBUTION ---")
    
    # Task 1: Generate the Website Template
    create_site_dashboard(analyzed_list)
    
    # Task 2: Dispatch Emails
    dispatch_to_subscribers(report_md)

    print("\n✅ Prototype Run Complete.")

if __name__ == "__main__":
    main()