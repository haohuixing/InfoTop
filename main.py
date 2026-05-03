import os
import subprocess
import pandas as pd
from sqlalchemy import text
from extraction_scripts.extract_revenue import sync_revenue_growth, engine
from process import run_analysis, format_to_markdown

# Import the new distribution modules
from web_generator import create_site_dashboard
from email_dispatcher import dispatch_to_subscribers

def main():
    # --- PHASE 0: FETCH PENDING ORDERS ---
    print("--- PHASE 0: CHECKING FOR ORDERS ---")
    
    # 1. Look for users who clicked 'Order' on your (future) website
    query = text("SELECT * FROM report_requests WHERE status = 'pending'")
    with engine.connect() as conn:
        orders_df = pd.read_sql(query, conn)

    if orders_df.empty:
        print("😴 No new orders found. Exiting.")
        return

    print(f"📦 Found {len(orders_df)} new orders to process.")

    # --- PHASE 1: GATHER (EXTRACTION) ---
    print("\n--- PHASE 1: EXTRACTION ---")
    
    # IMPORTANT: We REMOVED 'DROP TABLE' so we don't delete other users' history
    
    for index, row in orders_df.iterrows():
        ticker = row['ticker']
        user_email = row['user_email']
        order_id = row['id']
        
        try:
            print(f"🚀 Processing {ticker} for {user_email}...")
            sync_revenue_growth(ticker)
            
            # --- PHASE 2: PROCESS (ANALYSIS) ---
            # We fetch just THIS specific ticker from the tracker for analysis
            df = pd.read_sql(text(f"SELECT * FROM revenue_growth_tracker WHERE ticker = '{ticker}' ORDER BY id DESC LIMIT 1"), engine)
            analyzed_list = run_analysis(df)
            
            # --- PHASE 3: DISTRIBUTION ---
            # 1. Update the Email Dispatcher to send ONLY to the person who ordered it
            # Note: You will need to tweak email_dispatcher.py to accept a 'recipient' argument
            try:
                dispatch_to_subscribers(analyzed_list, recipient=user_email)
            except Exception as e:
                print(f"❌ Email Dispatch Error: {e}")

            # 2. Mark this order as COMPLETED in the database
            with engine.connect() as conn:
                conn.execute(text("UPDATE report_requests SET status = 'completed' WHERE id = :id"), {"id": order_id})
                conn.commit()
                print(f"✅ Order #{order_id} marked as completed.")

        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")

    # --- PHASE 4: UPDATE DASHBOARD & DEPLOY ---
    print("\n--- PHASE 4: UPDATING GLOBAL DASHBOARD ---")
    
    # We fetch ALL completed data to show on the public website
    all_data_df = pd.read_sql("SELECT * FROM revenue_growth_tracker", engine)
    full_analyzed_list = run_analysis(all_data_df)
    
    try:
        # Update the index.html with everyone's reports
        create_site_dashboard(full_analyzed_list)
        
        # Deploy updated site to Cloudflare
        print("🚀 Syncing updated dashboard to Cloudflare...")
        subprocess.run(["wrangler", "pages", "deploy", "dist", "--project-name", "market-intelligence"], check=True, shell=True)
        print("🌐 Live Site Updated!")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

    print("\n✅ WORKER CYCLE COMPLETE.")

if __name__ == "__main__":
    main()
