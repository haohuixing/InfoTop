import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

# This script creates BOTH tables needed for the app
sql_commands = [
    """
    CREATE TABLE IF NOT EXISTS report_requests (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        user_email VARCHAR(255) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS revenue_growth_tracker (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10),
        current_period VARCHAR(50),
        prior_period VARCHAR(50),
        revenue_current NUMERIC,
        revenue_prior NUMERIC,
        growth_pct NUMERIC,
        summary TEXT,
        sentiment VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
]

def init():
    try:
        with engine.connect() as conn:
            print("🔗 Connecting to Supabase...")
            for cmd in sql_commands:
                conn.execute(text(cmd))
            conn.commit()
            print("✅ Both tables ('report_requests' & 'revenue_growth_tracker') are ready!")
            
            # Double check: List the tables
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
            tables = [row[0] for row in result]
            print(f"📁 Current tables in DB: {tables}")

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    init()
