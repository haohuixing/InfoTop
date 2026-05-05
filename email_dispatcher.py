# email_dispatcher.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# We add 'recipient_email' as an optional argument
def dispatch_to_subscribers(analyzed_data, recipient_email=None):
    # 1. Credentials
    sender_email = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASS")
    
    # 2. Determine who gets the email
    # If a specific email is passed, send to that. Otherwise, use your test list.
    if recipient_email:
        subscribers = [recipient_email]
    else:
        subscribers = [] # Test list of whatever emails you want
        

    # --- UPDATED STEP 3: Build the HTML content ---
    # We change the title and add a "Thank you" note
    email_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; color: #333;">
        <h1 style="color: #2c3e50;">📈 Your Market Intelligence Report</h1>
        <p>Hello, here is the financial analysis you requested from our dashboard.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
    """

    for item in analyzed_data:
        # Define colors based on sentiment
        color = "#2ecc71" if item['sentiment'] == "Bullish" else "#e74c3c" if item['sentiment'] == "Cautious" else "#f1c40f"
        
        email_html += f"""
        <div style="margin-bottom: 30px; border-left: 6px solid {color}; padding-left: 20px;">
            <h2 style="margin: 0; font-size: 24px;">{item['ticker']} <span style="font-size: 16px; color: {color};">({item['sentiment']})</span></h2>
            <p style="font-size: 18px; margin: 10px 0;"><strong>Revenue Growth:</strong> {item['growth_pct']}%</p>
            <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; font-style: italic;">
                "{item['summary']}"
            </div>
        </div>
        """

    email_html += """
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #7f8c8d;">
            This report was automatically generated using SEC Edgar data. 
            View your full history at <a href="https://market-intelligence-9wc.pages.dev/">Market Intelligence Hub</a>.
        </p>
    </div>
    """

    # 4. The Sending Loop
    print(f"📧 Sending report to: {', '.join(subscribers)}...")
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)

        for recipient in subscribers:
            msg = MIMEMultipart()
            msg["From"] = f"Market Bot <{sender_email}>"
            msg["To"] = recipient
            msg["Subject"] = f"🚀 Your Requested Report: {analyzed_data[0]['ticker'] if analyzed_data else 'Update'}"
            
            msg.attach(MIMEText(email_html, "html"))
            server.sendmail(sender_email, recipient, msg.as_string())
            print(f"  >> Delivered to: {recipient}")

        server.quit()
        print("✨ Email dispatch successful!")

    except Exception as e:
        print(f"❌ Gmail Error: {e}")
