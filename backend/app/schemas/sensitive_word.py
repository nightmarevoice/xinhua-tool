from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class SensitiveWordGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    words: List[str]  # 敏感词列表

class SensitiveWordGroupCreate(SensitiveWordGroupBase):
    pass

class SensitiveWordGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    words: Optional[List[str]] = None

class SensitiveWordGroup(SensitiveWordGroupBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    created_at: datetime
    updated_at: datetime






