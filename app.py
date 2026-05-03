# app.py
import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Use your existing DB setup
engine = create_engine(os.getenv("DATABASE_URL")) # Or build URL like in your script

@app.get("/")
async def home(request: Request):
    # Fetch all completed reports to show on the dashboard
    with engine.connect() as conn:
        reports = pd.read_sql("SELECT * FROM revenue_growth_tracker ORDER BY id DESC", conn).to_dict(orient="records")
    return templates.TemplateResponse("index.html", {"request": request, "reports": reports})

@app.post("/order-report")
async def order_report(ticker: Form(...), email: Form(...)):
    # Save the request to the database
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO report_requests (ticker, user_email, status) VALUES (:t, :e, 'pending')"),
            {"t": ticker.upper(), "e": email}
        )
        conn.commit()
    return RedirectResponse(url="/?msg=Order+Received", status_code=303)