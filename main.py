import os
import subprocess # Necessary to run the wrangler command
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
    df = pd.read_sql("SELECT * FROM revenue_growth_tracker", engine)
    analyzed_list = run_analysis(df)
    report_md = format_to_markdown(analyzed_list)

    # --- PHASE 3: OUTPUT & DISTRIBUTION ---
    print("\n--- PHASE 3: OUTPUT & DISTRIBUTION ---")
    
    # 1. Create 'dist' directory if it doesn't exist (Safety Check)
    if not os.path.exists('dist'):
        os.makedirs('dist')
        print("📁 Created 'dist' folder for deployment.")

    # 2. Save local Markdown backup
    with open("latest_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)
        print("📝 Local Markdown report saved.")

    # 3. Generate the Website (now saving to dist/index.html)
    try:
        create_site_dashboard(analyzed_list)
    except Exception as e:
        print(f"❌ Web Generation Error: {e}")

    # 4. Dispatch Emails to Subscribers
    try:
        dispatch_to_subscribers(analyzed_list)
    except Exception as e:
        print(f"❌ Email Dispatch Error: {e}")

    """
    # --- PHASE 4: CLOUDFLARE DEPLOY ---
    print("\n--- PHASE 4: CLOUDFLARE DEPLOY ---")
    try:
        print("🚀 Uploading ONLY the 'dist' folder to Cloudflare Pages...")
        # This only uploads index.html, keeping your .env and scripts private
        subprocess.run(["wrangler", "pages", "deploy", "dist", "--project-name", "cloudflare name"], check=True)
        print("🌐 Live Site Updated!")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

    print("\n✅ ALL SYSTEMS GO.")
    """

if __name__ == "__main__":
    main()
