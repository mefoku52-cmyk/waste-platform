"""Use CMEP's declarative Base when available; standalone fallback for tests."""
try:
    from app.shared.infrastructure.db.base import Base
except ImportError:
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass
