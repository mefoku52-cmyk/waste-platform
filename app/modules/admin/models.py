from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AdminModel(BaseModel):
    id: Optional[int] = None
    created_at: datetime = datetime.now()
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
