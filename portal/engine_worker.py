# engine_worker.py
import time
from sqlalchemy import create_engine, text
from analysis import run_gemini_analysis
from extraction_scripts.extract_revenue import sync_revenue_growth # Your existing script

engine = create_engine(os.getenv("DATABASE_URL"))

def process_pending_orders():
    while True:
        with engine.connect() as conn:
            # Look for an order the website just created
            order = conn.execute(text("SELECT * FROM report_orders WHERE status = 'pending' LIMIT 1")).fetchone()
            
            if order:
                print(f"🛠️ Processing order for {order.ticker}...")
                
                # 1. Scrape SEC (Using your existing module)
                # Modify your sync_revenue_growth to return data instead of just saving
                raw_data = sync_revenue_growth(order.ticker)
                
                # 2. Analyze with Gemini
                analysis_result = run_gemini_analysis(
                    order.ticker, raw_data, order.indicator, order.weight
                )
                
                # 3. Save final report and mark as done
                conn.execute(text("""
                    INSERT INTO reports (user_id, ticker, summary) VALUES (1, :t, :s);
                    UPDATE report_orders SET status = 'completed' WHERE id = :id;
                """), {"t": order.ticker, "s": analysis_result, "id": order.id})
                conn.commit()
                
        time.sleep(10) # Check for new orders every 10 seconds

if __name__ == "__main__":
    process_pending_orders()