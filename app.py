import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

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
async def home(request: Request, msg: str = None):
    # Fetch recent reports for the "Intelligence Feed" module
    query = text("SELECT ticker, growth_pct, summary, sentiment FROM revenue_growth_tracker ORDER BY created_at DESC LIMIT 6")
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            reports = [dict(row) for row in result.mappings()]
    except:
        reports = []

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"reports": reports, "msg": msg, "base_url": BASE_URL}
    )

@app.post("/order-report")
async def order_report(ticker: str = Form(...), email: str = Form(...)):
    query = text("INSERT INTO report_requests (ticker, user_email, status) VALUES (:t, :e, 'pending')")
    with engine.connect() as conn:
        conn.execute(query, {"t": ticker.upper().strip(), "e": email.lower().strip()})
        conn.commit()
    return RedirectResponse(url="/?msg=Intelligence+Request+Received.+Check+Email+Shortly.", status_code=303)
