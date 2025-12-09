from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict
from datetime import datetime

class ModelParameterBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    name: str
    type: str  # string, number, boolean, array, object
    default_value: Any
    model_type: str  # proprietary, general
    description: str
    required: bool = False
    validation: Optional[Dict[str, Any]] = None

class ModelParameterCreate(ModelParameterBase):
    pass

class ModelParameterUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    name: Optional[str] = None
    type: Optional[str] = None
    default_value: Optional[Any] = None
    model_type: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    validation: Optional[Dict[str, Any]] = None

class ModelParameter(ModelParameterBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
