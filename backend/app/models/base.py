"""Základné databázové modely."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
import uuid

from app.core.database import Base


class BaseModel(Base):
    """Základný model so spoločnými stĺpcami."""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    is_active = Column(
        String,
        default=True,
        nullable=False,
        index=True,
    )
    
    @declared_attr
    def __tablename__(cls):
        """Generovanie názvu tabuľky z názvu triedy."""
        return cls.__name__.lower()
    
    def dict(self) -> dict:
        """Konverzia modelu na slovník."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
