from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InquiriesCreate(BaseModel):
    name: str
    description: Optional[str] = None

class InquiriesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class InquiriesResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
