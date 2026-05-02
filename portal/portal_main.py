# portal_main.py
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
engine = create_engine(os.getenv("DATABASE_URL")) # Your Postgres URL

@app.get("/")
async def dashboard(request: Request):
    # Fetch completed reports from Postgres to show the user
    with engine.connect() as conn:
        reports = conn.execute(text("SELECT * FROM reports WHERE user_id = 1")).fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "reports": reports})

@app.post("/order")
async def create_order(
    ticker: str = Form(...), 
    indicator: str = Form(...), 
    weight: int = Form(...)
):
    # Save the 'Order' to Postgres. 
    # Your separate Engine will watch this table and process it.
    query = text("""
        INSERT INTO report_orders (ticker, indicator, weight, status) 
        VALUES (:t, :i, :w, 'pending')
    """)
    with engine.connect() as conn:
        conn.execute(query, {"t": ticker.upper(), "i": indicator, "w": weight})
        conn.commit()
    
    return {"message": "Report ordered! Check back in a minute."}