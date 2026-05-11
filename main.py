# main.py

import os
import pandas as pd
from sqlalchemy import text
from extraction_scripts.extract_revenue import sync_revenue_growth, engine
from process import run_analysis
from email_dispatcher import dispatch_to_subscribers

def main():
    print("--- PHASE 0: CHECKING FOR ORDERS ---")
    query = text("SELECT * FROM report_requests WHERE status = 'pending'")
    with engine.connect() as conn:
        orders_df = pd.read_sql(query, conn)

    if orders_df.empty:
        print("😴 No pending orders.")
        return

    for index, row in orders_df.iterrows():
        ticker = row['ticker']
        user_email = row['user_email']
        order_id = row['id']
        
        try:
            sync_revenue_growth(ticker)
            df = pd.read_sql(text(f"SELECT * FROM revenue_growth_tracker WHERE ticker = '{ticker}' ORDER BY id DESC LIMIT 1"), engine)
            analyzed_list = run_analysis(df)
            analysis = analyzed_list[0]

            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE revenue_growth_tracker SET sentiment = :s, summary = :sum WHERE ticker = :t"),
                    {"s": analysis['sentiment'], "sum": analysis['summary'], "t": ticker}
                )
                conn.execute(text("UPDATE report_requests SET status = 'completed' WHERE id = :id"), {"id": order_id})
                conn.commit()

            dispatch_to_subscribers(analyzed_list, recipient_email=user_email)
            print(f"✅ Completed: {ticker}")
        except Exception as e:
            print(f"❌ Error on {ticker}: {e}")

if __name__ == "__main__":
    main()
