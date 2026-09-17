import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Find .env in backend directory or parent
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pinlytics.db")

# Setup engine arguments depending on DB type
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

if DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

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
    
    # Safe SQLite column migrations for new columns if table already exists
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(customers)"))
            cols = [r[1] for r in res.fetchall()]
            
            if "district_id" not in cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN district_id INTEGER REFERENCES district_master(id)"))
                    conn.commit()
                except Exception as e:
                    print(f"Note on adding district_id column: {e}")

            if "district_resolution_source" not in cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN district_resolution_source VARCHAR(50) DEFAULT 'UNRESOLVED'"))
                    conn.commit()
                except Exception as e:
                    print(f"Note on adding district_resolution_source column: {e}")

            if "source_district" not in cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN source_district VARCHAR(255)"))
                    conn.commit()
                except Exception as e:
                    print(f"Note on adding source_district column: {e}")

            if "district_mismatch" not in cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN district_mismatch BOOLEAN DEFAULT 0"))
                    conn.commit()
                except Exception as e:
                    print(f"Note on adding district_mismatch column: {e}")

            if "source_file_name" not in cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN source_file_name VARCHAR(255)"))
                    conn.commit()
                except Exception as e:
                    print(f"Note on adding source_file_name column: {e}")

            if "source_row_number" not in cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN source_row_number INTEGER"))
                    conn.commit()
                except Exception as e:
                    print(f"Note on adding source_row_number column: {e}")

            if "raw_row_data" not in cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN raw_row_data TEXT"))
                    conn.commit()
                except Exception as e:
                    print(f"Note on adding raw_row_data column: {e}")
        except Exception as e:
            print(f"Database schema check notice: {e}")

    # Seed 14 Kerala canonical master districts and migrate existing records
    from app.services.district_resolution_service import DistrictResolutionService
    db = SessionLocal()
    try:
        DistrictResolutionService.migrate_existing_data(db)
    finally:
        db.close()
