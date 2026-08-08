from app.shared.database.db import engine, Base
from app.shared.models.base import User, Inquiry
import logging

logger = logging.getLogger(__name__)

def create_tables():
    """Vytvorí všetky tabuľky v databáze"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Databázové tabuľky vytvorené")
        return True
    except Exception as e:
        logger.error(f"❌ Chyba pri vytváraní tabuliek: {e}")
        return False

def drop_tables():
    """Odstráni všetky tabuľky (len pre vývoj!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Databázové tabuľky odstránené")
        return True
    except Exception as e:
        logger.error(f"❌ Chyba pri odstraňovaní tabuliek: {e}")
        return False
