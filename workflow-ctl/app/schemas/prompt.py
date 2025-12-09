from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PromptBase(BaseModel):
    title: str
    system_prompt: Optional[str] = None  # 系统提示词
    user_prompt: Optional[str] = None  # 用户提示词
    model_type: str

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model_type: Optional[str] = None

class Prompt(PromptBase):
    id: int
    external_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# 同步接口使用的 Schema
class PromptSync(BaseModel):
    """用于 backend 同步的 Prompt Schema"""
    external_id: int  # backend 系统的 ID
    title: str
    system_prompt: Optional[str] = None  # 系统提示词
    user_prompt: Optional[str] = None  # 用户提示词
    model_type: str


