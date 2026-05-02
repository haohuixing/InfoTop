import os
import sys
import time
import google.generativeai as genai
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Path setup to import your existing extraction scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extraction_scripts.extract_revenue import sync_revenue_growth

load_dotenv(dotenv_path="../.env")

# Config
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
db = create_engine(os.getenv("DATABASE_URL"))

def run_worker():
    print("🤖 AI Engine Worker is Online. Monitoring Postgres...")
    
    while True:
        with db.connect() as conn:
            # 1. Fetch one pending order
            order = conn.execute(text("SELECT * FROM report_orders WHERE status = 'pending' LIMIT 1")).fetchone()
            
            if order:
                print(f"⚙️ Processing order: {order.ticker}...")
                conn.execute(text("UPDATE report_orders SET status = 'processing' WHERE id = :id"), {"id": order.id})
                conn.commit()

                try:
                    # 2. Scrape SEC Data
                    # (Note: Ensure your sync_revenue_growth returns the data string)
                    raw_financial_data = sync_revenue_growth(order.ticker)

                    # 3. Analyze with Gemini
                    prompt = f"""
                    Analyze the following SEC revenue data for {order.ticker}:
                    {raw_financial_data}
                    
                    Focus Indicator: {order.indicator}
                    User Weighting: {order.weight}/100
                    
                    Provide a concise 3-sentence investment summary.
                    """
                    response = model.generate_content(prompt)
                    analysis = response.text

                    # 4. Save Final Report
                    conn.execute(
                        text("INSERT INTO reports (ticker, analysis_text) VALUES (:t, :a)"),
                        {"t": order.ticker, "a": analysis}
                    )
                    conn.execute(text("UPDATE report_orders SET status = 'completed' WHERE id = :id"), {"id": order.id})
                    conn.commit()
                    print(f"✅ Success: {order.ticker} analysis complete.")

                except Exception as e:
                    print(f"❌ Error processing {order.ticker}: {e}")
                    conn.execute(text("UPDATE report_orders SET status = 'failed' WHERE id = :id"), {"id": order.id})
                    conn.commit()

        time.sleep(10) # Wait 10 seconds before checking again

if __name__ == "__main__":
    run_worker()
