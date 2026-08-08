from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Databázová URL - momentálne SQLite (pre testovanie)
# Neskôr ľahko zmeníš na PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./waste_platform.db"  # SQLite pre jednoduchosť
)

# Vytvorenie engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pre modely
Base = declarative_base()

# Závislosť pre FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
