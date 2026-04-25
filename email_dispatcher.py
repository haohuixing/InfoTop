# email_dispatcher.py
import os
import resend
from dotenv import load_dotenv

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

def dispatch_to_subscribers(analyzed_data):
    """
    Sends a styled HTML email to your subscriber list using Resend.
    """
    # 1. Real Subscriber List
    # STARTING TIP: Put your own email here first to test!
    subscribers = ["343906699@Tdsb.ca", "a27131023905831@gmail.com"] 

    # 2. Build the HTML body for the email
    email_html = "<h1>📈 Market Intelligence Daily</h1>"
    email_html += "<p>Here is your automated SEC revenue growth report:</p><hr>"
    
    for item in analyzed_data:
        color = "#2ecc71" if item['sentiment'] == "Bullish" else "#e74c3c" if item['sentiment'] == "Cautious" else "#f1c40f"
        email_html += f"""
        <div style="margin-bottom: 20px; border-left: 4px solid {color}; padding-left: 15px;">
            <h2 style="margin: 0;">{item['ticker']} - <span style="color: {color};">{item['sentiment']}</span></h2>
            <p><strong>Revenue Growth:</strong> {item['growth_pct']}%</p>
            <p><em>{item['summary']}</em></p>
        </div>
        """
    
    email_html += "<br><p><small>Sent via your Automated Intelligence Pipeline</small></p>"

    print(f"📧 Attempting to send {len(subscribers)} emails...")

    # 3. Send the emails
    try:
        params = {
            "from": "MarketBot <onboarding@resend.dev>", # Resend provides this for testing
            "to": subscribers,
            "subject": "🚀 New Market Intelligence Report Available",
            "html": email_html,
        }

        email = resend.Emails.send(params)
        print(f"✨ Success! Email ID: {email['id']}")
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
