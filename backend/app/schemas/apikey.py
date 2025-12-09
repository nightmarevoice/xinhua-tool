from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ApiKeyBase(BaseModel):
    name: str
    description: Optional[str] = None

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ApiKey(ApiKeyBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    key: str
    status: str
    created_at: datetime
    updated_at: datetime
