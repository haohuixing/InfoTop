# email_dispatcher.py

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def dispatch_to_subscribers(analyzed_data, recipient_email=None):
    sender_email = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASS")
    base_url = os.getenv("BASE_URL", "https://infotop.onrender.com")
    
    subscribers = [recipient_email] if recipient_email else []
    if not subscribers: return

    email_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; color: #333;">
        <h1 style="color: #2c3e50;">📈 Your Market Intelligence Report</h1>
        <p>Hello, here is the financial analysis you requested.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
    """

    for item in analyzed_data:
        color = "#2ecc71" if item['sentiment'] == "Bullish" else "#e74c3c" if item['sentiment'] == "Cautious" else "#f1c40f"
        email_html += f"""
        <div style="margin-bottom: 30px; border-left: 6px solid {color}; padding-left: 20px;">
            <h2 style="margin: 0; font-size: 24px;">{item['ticker']} ({item['sentiment']})</h2>
            <p style="font-size: 18px;"><strong>Revenue Growth:</strong> {item['growth_pct']}%</p>
            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; font-style: italic;">"{item['summary']}"</div>
        </div>
        """

    email_html += f"""
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #7f8c8d;">
            Report generated via SEC Edgar data. 
            View dashboard: <a href="{base_url}">{base_url}</a>
        </p>
    </div>
    """

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        for recipient in subscribers:
            msg = MIMEMultipart()
            msg["From"] = f"Market Bot <{sender_email}>"
            msg["To"] = recipient
            msg["Subject"] = f"🚀 Your Report: {analyzed_data[0]['ticker']}"
            msg.attach(MIMEText(email_html, "html"))
            server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        print("✨ Emails sent!")
    except Exception as e:
        print(f"❌ Gmail Error: {e}")
