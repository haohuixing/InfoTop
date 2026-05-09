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
    # ADD THIS LINE at the very beginning of main()
    os.makedirs('dist', exist_ok=True) 
    
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
                dispatch_to_subscribers(analyzed_list, recipient_email=user_email)
            except Exception as e:
                print(f"❌ Email Dispatch Error: {e}")

            # 2. Mark this order as COMPLETED in the database
            with engine.connect() as conn:
                conn.execute(text("UPDATE report_requests SET status = 'completed' WHERE id = :id"), {"id": order_id})
                conn.commit()
                print(f"✅ Order #{order_id} marked as completed.")

        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")


    print("\n✅ WORKER CYCLE COMPLETE.")

if __name__ == "__main__":
    main()
