from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PromptBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    title: str
    system_prompt: Optional[str] = None  # 系统提示词
    user_prompt: Optional[str] = None  # 用户提示词
    model_type: str  # proprietary, general

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model_type: Optional[str] = None

class Prompt(PromptBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
