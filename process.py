import pandas as pd

def run_analysis(df):
    """
    Takes raw DB data and adds Sentiment and Summary.
    """
    results = []
    
    for _, row in df.iterrows():
        ticker = row['ticker']
        growth = row['growth_pct']
        
        # --- ANALYSIS LOGIC ---
        if growth > 15:
            sentiment = "Bullish"
            summary = f"{ticker} is outperforming with {growth}% revenue growth. Momentum is strong."
        elif growth > 0:
            sentiment = "Neutral"
            summary = f"{ticker} shows stable growth of {growth}%. Consistent performance."
        else:
            sentiment = "Cautious"
            summary = f"{ticker} revenue contracted by {abs(growth)}%. Need to check SEC risk factors."

        combined = {
            **row.to_dict(),
            "sentiment": sentiment,
            "summary": summary
        }
        results.append(combined)
        
    return results
