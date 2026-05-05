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

# --- DATABASE SETUP ---
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT") or 5432),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

@app.get("/")
async def home(request: Request):
    with engine.connect() as conn:
        try:
            reports = pd.read_sql("SELECT * FROM revenue_growth_tracker ORDER BY ticker ASC", conn).to_dict(orient="records")
        except:
            reports = []
            
    msg = request.query_params.get("msg")
    return templates.TemplateResponse("index.html", {"request": request, "reports": reports, "msg": msg})

@app.post("/order-report", response_model=None)
async def order_report(ticker: str = Form(...), email: str = Form(...)) -> RedirectResponse:
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO report_requests (ticker, user_email, status) VALUES (:t, :e, 'pending')"),
            {"t": ticker.upper().strip(), "e": email.strip()}
        )
        conn.commit()
    
    print(f"📥 New Order Received: {ticker} for {email}")
    return RedirectResponse(url="/?msg=Success!+Your+report+is+being+processed.", status_code=303)
