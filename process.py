import pandas as pd

def run_analysis(df):
    """
    This function takes the raw data from the DB and 
    runs the 'Analysis' logic (currently a mock filler).
    """
    results = []
    
    print(f"🤖 Processing {len(df)} records...")

    for _, row in df.iterrows():
        ticker = row['ticker']
        growth = row['growth_pct']
        
        # --- MOCK LLM LOGIC (Switch this to OpenAI/Claude later) ---
        if growth > 15:
            sentiment = "Bullish"
            summary = f"{ticker} is outperforming with {growth}% growth. Momentum is strong."
        elif growth > 0:
            sentiment = "Neutral"
            summary = f"{ticker} shows stable growth of {growth}%. Consistent performance."
        else:
            sentiment = "Cautious"
            summary = f"{ticker} revenue contracted by {abs(growth)}%. Need to check 10-K risk factors."

        # Merge the original data with our analysis
        combined = {
            **row.to_dict(),
            "sentiment": sentiment,
            "summary": summary
        }
        results.append(combined)
        
    return results

def format_to_markdown(analyzed_data):
    """
    Turns the analyzed list into a clean Markdown string.
    """
    md = "# 📈 Market Intelligence Report\n\n"
    for item in analyzed_data:
        md += f"### {item['ticker']} | {item['sentiment']}\n"
        md += f"- **Growth:** {item['growth_pct']}%\n"
        md += f"- **Analysis:** {item['summary']}\n\n"
        md += "---\n"
    return md