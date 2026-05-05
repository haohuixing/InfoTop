# app.py
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- DATABASE SETUP (Matches your extraction script) ---
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

@app.get("/")
async def home(request: Request):
    # Fetch all completed reports to show on the dashboard
    with engine.connect() as conn:
        try:
            # We join with our analysis logic or just show the tracker data
            reports = pd.read_sql("SELECT * FROM revenue_growth_tracker ORDER BY ticker ASC", conn).to_dict(orient="records")
        except:
            reports = [] # If table is empty
            
    # Check for a success message in the URL
    msg = request.query_params.get("msg")
    return templates.TemplateResponse("index.html", {"request": request, "reports": reports, "msg": msg})

@app.post("/order-report")
async def order_report(ticker: Form(...), email: Form(...)):
    # 1. Save the request to the database as 'pending'
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO report_requests (ticker, user_email, status) VALUES (:t, :e, 'pending')"),
            {"t": ticker.upper().strip(), "e": email.strip()}
        )
        conn.commit()
    
    print(f"📥 New Order Received: {ticker} for {email}")
    
    # 2. Redirect back home with a success message
    return RedirectResponse(url="/?msg=Success!+Your+report+is+being+processed.", status_code=303)
