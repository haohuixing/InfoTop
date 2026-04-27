# email_dispatcher.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def dispatch_to_subscribers(analyzed_data):
    # 1. Credentials
    sender_email = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASS")
    
    # 2. Your Subscriber List (NO LIMITS on who you add here!)
    subscribers = [
        "example@example.com"
    ]

    # 3. Build the HTML content
    email_html = "<h1>📈 Market Intelligence Daily</h1>"
    for item in analyzed_data:
        color = "#2ecc71" if item['sentiment'] == "Bullish" else "#e74c3c" if item['sentiment'] == "Cautious" else "#f1c40f"
        email_html += f"""
        <div style="margin-bottom: 20px; border-left: 4px solid {color}; padding-left: 15px;">
            <h2 style="margin: 0;">{item['ticker']} - <span style="color: {color};">{item['sentiment']}</span></h2>
            <p><strong>Revenue Growth:</strong> {item['growth_pct']}%</p>
            <p><em>{item['summary']}</em></p>
        </div>
        """

    # 4. The Sending Loop
    print(f"📧 Sending via Gmail to {len(subscribers)} subscribers...")
    
    try:
        # Connect to Google's Server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls() # Secure the connection
        server.login(sender_email, password)

        for recipient in subscribers:
            # Create the email container
            msg = MIMEMultipart()
            msg["From"] = f"Market Bot <{sender_email}>"
            msg["To"] = recipient
            msg["Subject"] = "🚀 New Market Intelligence Report"
            
            msg.attach(MIMEText(email_html, "html"))
            
            # Send it!
            server.sendmail(sender_email, recipient, msg.as_string())
            print(f"  >> Delivered to: {recipient}")

        server.quit()
        print("✨ All emails sent successfully!")

    except Exception as e:
        print(f"❌ Gmail Error: {e}")
