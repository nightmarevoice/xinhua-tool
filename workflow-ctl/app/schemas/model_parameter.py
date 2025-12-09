from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict
from datetime import datetime

class ModelParameterBase(BaseModel):
    name: str
    type: str
    default_value: Any
    model_type: str
    description: str
    required: bool = False
    validation: Optional[Dict[str, Any]] = None

class ModelParameterCreate(ModelParameterBase):
    pass

class ModelParameterUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    default_value: Optional[Any] = None
    model_type: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    validation: Optional[Dict[str, Any]] = None

class ModelParameter(ModelParameterBase):
    id: int
    external_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# 同步接口使用的 Schema
class ModelParameterSync(BaseModel):
    """用于 backend 同步的 ModelParameter Schema"""
    external_id: int  # backend 系统的 ID
    name: str
    type: str
    default_value: Any
    model_type: str
    description: str
    required: bool = False
    validation: Optional[Dict[str, Any]] = None


