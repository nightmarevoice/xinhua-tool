from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ApiKeyBase(BaseModel):
    name: str
    description: Optional[str] = None
    key: str
    status: str = "active"

class ApiKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    key: str

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ApiKey(ApiKeyBase):
    id: int
    external_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# 同步接口使用的 Schema
class ApiKeySync(BaseModel):
    """用于 backend 同步的 API Key Schema"""
    external_id: int  # backend 系统的 ID
    name: str
    description: Optional[str] = None
    key: str
    status: str = "active"


