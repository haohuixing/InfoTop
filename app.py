import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# 1. SETUP & CONFIG
load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Website URL for links (defaults to localhost if not set in Render)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# 2. DATABASE CONNECTION
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

# 3. ROUTES

@app.get("/")
async def home(request: Request, msg: str = None):
    """Displays the dashboard with the 10 most recent reports."""
    query = text("""
        SELECT ticker, growth_pct, summary 
        FROM revenue_growth_tracker 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            reports = [dict(row) for row in result.mappings()]
    except Exception as e:
        print(f"❌ Dashboard DB Error: {e}")
        reports = []

    # Updated TemplateResponse to fix the 'tuple/dict' error
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "reports": reports, 
            "msg": msg, 
            "base_url": BASE_URL
        }
    )

@app.post("/order-report")
async def order_report(ticker: str = Form(...), email: str = Form(...)):
    """Handles new report requests from the dashboard form."""
    query = text("""
        INSERT INTO report_requests (ticker, user_email, status) 
        VALUES (:t, :e, 'pending')
    """)
    
    try:
        with engine.connect() as conn:
            conn.execute(
                query, 
                {"t": ticker.upper().strip(), "e": email.lower().strip()}
            )
            conn.commit()
    except Exception as e:
        print(f"❌ Order Submission Error: {e}")
        return RedirectResponse(url="/?msg=Error+saving+order.", status_code=303)

    # Redirects back to home page with a success message
    return RedirectResponse(
        url="/?msg=Success!+Report+is+being+generated.", 
        status_code=303
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
