#!/usr/bin/env python3
from app.shared.database.db import engine
from app.shared.models.base import User, Inquiry
from app.shared.database.migrations import create_tables
import logging

logging.basicConfig(level=logging.INFO)

def init_database():
    """Inicializuje databázu s počiatočnými dátami"""
    print("🔧 Inicializácia databázy...")
    
    # Vytvor tabuľky
    if not create_tables():
        print("❌ Chyba pri vytváraní tabuliek")
        return False
    
    print("✅ Tabuľky vytvorené")
    print("💡 Databáza je pripravená na použitie")
    print("   - SQLite: ./waste_platform.db")
    print("   - Modely: User, Inquiry")
    print("   - Pre PostgreSQL zmeň DATABASE_URL v .env")
    
    return True

if __name__ == "__main__":
    init_database()
