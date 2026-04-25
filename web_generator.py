# web_generator.py

def create_site_dashboard(analyzed_data):
    """
    Generates a professional HTML/CSS dashboard for web display.
    """
    # Logic to map sentiments to CSS classes
    sentiment_colors = {
        "Bullish": "#2ecc71",   # Green
        "Neutral": "#f1c40f",   # Yellow
        "Cautious": "#e74c3c"   # Red
    }

    html_cards = ""
    for item in analyzed_data:
        color = sentiment_colors.get(item['sentiment'], "#7f8c8d")
        
        html_cards += f"""
        <div class="card" style="border-top: 6px solid {color};">
            <div class="header">
                <span class="ticker">{item['ticker']}</span>
                <span class="badge" style="background: {color};">{item['sentiment']}</span>
            </div>
            <div class="growth">Growth: {item['growth_pct']}%</div>
            <p class="summary">{item['summary']}</p>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Market Intelligence Hub</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
            .container {{ max-width: 900px; margin: auto; }}
            h1 {{ border-bottom: 2px solid #1e293b; padding-bottom: 10px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 30px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 12px; transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-5px); }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .ticker {{ font-size: 1.5rem; font-weight: bold; color: #38bdf8; }}
            .badge {{ padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; color: #000; }}
            .growth {{ font-size: 1.1rem; margin-bottom: 10px; color: #94a3b8; }}
            .summary {{ color: #cbd5e1; font-size: 0.95rem; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 Market Intelligence Hub</h1>
            <p>Automated Financial Analysis Dashboard</p>
            <div class="grid">
                {html_cards}
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print("🌐 Website: 'index.html' generated successfully.")
