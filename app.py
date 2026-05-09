import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles  # Added for Logo support
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- STATIC FILES SETUP ---
# This tells FastAPI to serve the 'images' folder at the '/images' URL
if not os.path.exists("images"):
    os.makedirs("images")
app.mount("/images", StaticFiles(directory="images"), name="images")

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
    query = text("""
        SELECT ticker, growth_pct, summary, sentiment 
        FROM revenue_growth_tracker 
        ORDER BY created_at DESC 
        LIMIT 6
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            reports = [dict(row) for row in result.mappings()]
    except Exception as e:
        print(f"❌ DB Error: {e}")
        reports = []

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"reports": reports, "msg": msg, "base_url": BASE_URL}
    )

@app.post("/order-report")
async def order_report(ticker: str = Form(...), email: str = Form(...)):
    query = text("INSERT INTO report_requests (ticker, user_email, status) VALUES (:t, :e, 'pending')")
    try:
        with engine.connect() as conn:
            conn.execute(query, {"t": ticker.upper().strip(), "e": email.lower().strip()})
            conn.commit()
    except Exception as e:
        print(f"❌ Order Error: {e}")
        return RedirectResponse(url="/?msg=Database+Error.", status_code=303)

    return RedirectResponse(url="/?msg=Intelligence+Request+Received.+Check+Email+Shortly.", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
