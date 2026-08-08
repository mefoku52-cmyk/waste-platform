from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app.shared.database.db import Base

class TimestampMixin:
    """Mixin pre timestampy"""
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # V produkcii hashované
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    permissions = Column(String(500), default="read_own,write_own")  # CSV
    is_active = Column(Boolean, default=True)

class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    registration_number = Column(String(50))
    vat_number = Column(String(50))
    address = Column(String(500))
    city = Column(String(100))
    country = Column(String(100))
    status = Column(String(50), default="active")

# ✅ PRÁVE SOM TI DOPLNIL CHÝBAJÚCU TABUĽKU
class CompanyMembership(Base, TimestampMixin):
    __tablename__ = "company_memberships"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")
    status = Column(String(50), default="active")

class Inquiry(Base, TimestampMixin):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="open")

class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))
    file_size = Column(Integer, default=0)
    status = Column(String(50), default="active")

class Compliance(Base, TimestampMixin):
    __tablename__ = "compliance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")
    priority = Column(String(20), default="medium")
    due_date = Column(DateTime, nullable=True)

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

class Analytics(Base, TimestampMixin):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_name = Column(String(255), nullable=False)
    event_data = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))

class Listing(Base, TimestampMixin):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    price = Column(Integer, default=0)
    currency = Column(String(10), default="EUR")
    status = Column(String(50), default="active")
    location = Column(String(255))

class AdminLog(Base, TimestampMixin):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50))
    target_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(45))
