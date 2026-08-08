from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ComplianceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ComplianceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ComplianceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
