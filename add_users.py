#!/usr/bin/env python3
from app.shared.database.db import SessionLocal
from app.shared.models.base import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_users():
    """Pridá testovacích používateľov do databázy"""
    db = SessionLocal()
    
    users = [
        {
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "Admin User",
            "role": "admin",
            "permissions": "read_all,write_all,delete_all,manage_users",
            "is_active": True
        },
        {
            "email": "manager@example.com",
            "password": "manager123",
            "full_name": "Manager User",
            "role": "manager",
            "permissions": "read_all,write_own,manage_team",
            "is_active": True
        },
        {
            "email": "user@example.com",
            "password": "user123",
            "full_name": "Regular User",
            "role": "user",
            "permissions": "read_own,write_own",
            "is_active": True
        }
    ]
    
    added = 0
    for user_data in users:
        # Skontroluj či už existuje
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            logger.info(f"⚠️ Používateľ {user_data['email']} už existuje")
            continue
        
        # Vytvor nového používateľa
        user = User(**user_data)
        db.add(user)
        added += 1
        logger.info(f"✅ Pridaný používateľ: {user_data['email']} (role: {user_data['role']})")
    
    db.commit()
    db.close()
    
    logger.info(f"✅ Celkom pridaných: {added} používateľov")
    return added

if __name__ == "__main__":
    add_users()
