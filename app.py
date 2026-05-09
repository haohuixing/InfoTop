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

# Master URL from .env
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
    query = text("SELECT ticker, growth_pct, summary FROM revenue_growth_tracker ORDER BY created_at DESC LIMIT 10")
    with engine.connect() as conn:
        result = conn.execute(query)
        reports = [dict(row) for row in result.mappings()]

    # UPDATE THIS PART BELOW:
    return templates.TemplateResponse(
        request=request,              # First argument must be request
        name="index.html",            # Second is the template name
        context={                     # Third is the data dictionary
            "reports": reports, 
            "msg": msg, 
            "base_url": BASE_URL
        }
    )
@app.post("/order-report")
async def order_report(ticker: str = Form(...), email: str = Form(...)):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO report_requests (ticker, user_email, status) VALUES (:t, :e, 'pending')"),
            {"t": ticker.upper().strip(), "e": email.lower().strip()}
        )
        conn.commit()
    return RedirectResponse(url="/?msg=Success!+Report+is+being+generated.", status_code=303)
