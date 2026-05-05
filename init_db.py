# init_db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()


# 1. Setup connection (using your existing logic)
connection_url = URL.create(
    drivername="postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)
engine = create_engine(connection_url)

# 2. The SQL command to create the orders table
# We use 'IF NOT EXISTS' so it doesn't error out if you run it twice
create_table_query = """
CREATE TABLE IF NOT EXISTS report_requests (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init():
    try:
        with engine.connect() as conn:
            print("🔗 Connecting to database...")
            conn.execute(text(create_table_query))
            conn.commit()
            print("✅ Table 'report_requests' is ready!")
            
            # Double check: List the tables
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
            tables = [row[0] for row in result]
            print(f"📁 Current tables in DB: {tables}")

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    init()
