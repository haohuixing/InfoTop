import os
import sys
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Allow importing from the root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extraction_scripts.extract_revenue import sync_revenue_growth

load_dotenv(dotenv_path="../.env")
engine = create_engine(os.getenv("DATABASE_URL"))

def start_worker():
    print("🤖 Engine Worker started. Watching for orders...")
    while True:
        with engine.connect() as conn:
            # 1. Look for a pending order
            order = conn.execute(text("SELECT * FROM report_orders WHERE status = 'pending' LIMIT 1")).fetchone()
            
            if order:
                print(f"⚙️ Processing {order.ticker}...")
                
                # 2. Run Extraction (Your existing script)
                # Note: You might want to modify sync_revenue_growth to return values
                sync_revenue_growth(order.ticker)
                
                # 3. Placeholder for Analysis (Gemini logic will go here later)
                mock_analysis = f"Analysis for {order.ticker} based on {order.indicator} (Weight: {order.weight})"

                # 4. Save to Reports table and update status
                conn.execute(
                    text("INSERT INTO reports (ticker, analysis_text) VALUES (:t, :a)"),
                    {"t": order.ticker, "a": mock_analysis}
                )
                conn.execute(
                    text("UPDATE report_orders SET status = 'completed' WHERE id = :id"),
                    {"id": order.id}
                )
                conn.commit()
                print(f"✅ Finished {order.ticker}")

        time.sleep(10) # Wait 10 seconds before checking again

if __name__ == "__main__":
    start_worker()
