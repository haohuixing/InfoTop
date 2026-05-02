import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env") # Look for .env in the root

app = FastAPI()
# Assuming you create a 'templates' folder inside 'portal'
templates = Jinja2Templates(directory="templates") 
engine = create_engine(os.getenv("DATABASE_URL"))

@app.get("/")
async def dashboard(request: Request):
    with engine.connect() as conn:
        # Get pending orders and completed reports
        orders = conn.execute(text("SELECT * FROM report_orders WHERE status = 'pending'")).fetchall()
        reports = conn.execute(text("SELECT * FROM reports ORDER BY created_at DESC")).fetchall()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "orders": orders,
        "reports": reports
    })

@app.post("/order")
async def create_order(ticker: str = Form(...), indicator: str = Form(...), weight: int = Form(...)):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO report_orders (ticker, indicator, weight) VALUES (:t, :i, :w)"),
            {"t": ticker.upper(), "i": indicator, "w": weight}
        )
        conn.commit()
    return RedirectResponse(url="/", status_code=303)
