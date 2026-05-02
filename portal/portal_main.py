import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")
app = FastAPI()
templates = Jinja2Templates(directory="templates")
db = create_engine(os.getenv("DATABASE_URL"))

@app.get("/")
async def dashboard(request: Request):
    with db.connect() as conn:
        # Fetch pending orders and completed reports
        orders = conn.execute(text("SELECT * FROM report_orders WHERE status != 'completed' ORDER BY created_at DESC")).fetchall()
        reports = conn.execute(text("SELECT * FROM reports ORDER BY created_at DESC")).fetchall()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "orders": orders,
        "reports": reports
    })

@app.post("/order")
async def create_order(ticker: str = Form(...), indicator: str = Form(...), weight: int = Form(...)):
    with db.connect() as conn:
        conn.execute(
            text("INSERT INTO report_orders (ticker, indicator, weight) VALUES (:t, :i, :w)"),
            {"t": ticker.upper(), "i": indicator, "w": weight}
        )
        conn.commit()
    return RedirectResponse(url="/", status_code=303)
