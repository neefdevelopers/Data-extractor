import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Find .env in backend directory or parent
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pinlytics.db")

# Setup engine arguments depending on DB type
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    # Safe SQLite column migration for district_id if table already exists
    with engine.connect() as conn:
        try:
            res = conn.execute(conn.connection.cursor().execute if hasattr(conn.connection, "cursor") else None or text("PRAGMA table_info(customers)"))
        except Exception:
            from sqlalchemy import text
            res = conn.execute(text("PRAGMA table_info(customers)"))
        cols = [r[1] for r in res.fetchall()]
        if "district_id" not in cols:
            from sqlalchemy import text
            try:
                conn.execute(text("ALTER TABLE customers ADD COLUMN district_id INTEGER REFERENCES district_master(id)"))
                conn.commit()
            except Exception as e:
                print(f"Note on adding district_id column: {e}")

    # Seed districts and migrate existing customer records
    from app.services.district_service import DistrictService
    db = SessionLocal()
    try:
        DistrictService.migrate_existing_data(db)
    finally:
        db.close()

