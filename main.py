import pandas as pd
from extraction_scripts.extract_revenue import sync_revenue_growth, engine
from process import run_analysis, format_to_markdown # Import from your process script
from sqlalchemy import text

def main():
    # PHASE 1: GATHER
    print("--- PHASE 1: EXTRACTION ---")
    watchlist = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL']
    
    # Optional: Clear table for fresh run
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_growth_tracker;"))
        conn.commit()

    for ticker in watchlist:
        sync_revenue_growth(ticker)

    # PHASE 2: PROCESS (The logic you just moved to process.py)
    print("\n--- PHASE 2: PROCESSING & ANALYSIS ---")
    df = pd.read_sql("SELECT * FROM revenue_growth_tracker", engine)
    
    # Use your new process module
    analyzed_list = run_analysis(df)
    report_md = format_to_markdown(analyzed_list)

    # PHASE 3: OUTPUT
    print("\n--- PHASE 3: OUTPUT ---")
    with open("latest_report.md", "w") as f:
        f.write(report_md)
    
    print("✅ Done! Check 'latest_report.md' for results.")

if __name__ == "__main__":
    main()