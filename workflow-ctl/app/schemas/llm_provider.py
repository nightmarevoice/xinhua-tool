from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime

class ModelConfiguration(BaseModel):
    """模型配置"""
    name: str
    max_input_tokens: int
    supports_function_calling: bool

class LLMProviderBase(BaseModel):
    name: str
    provider: str  # openai, azure, anthropic, google, custom
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    custom_config: Optional[Dict[str, str]] = None
    default_model_name: str
    fast_default_model_name: Optional[str] = None
    deployment_name: Optional[str] = None
    default_vision_model: Optional[str] = None
    model_configurations: Optional[List[ModelConfiguration]] = None
    category: str = 'general'  # general, professional
    is_default_provider: bool = False
    is_default_vision_provider: bool = False

class LLMProvider(LLMProviderBase):
    id: int
    external_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# 同步接口使用的 Schema
class LLMProviderSync(BaseModel):
    """用于 backend 同步的 LLM Provider Schema"""
    external_id: int  # backend 系统的 ID
    name: str
    provider: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    custom_config: Optional[Dict[str, str]] = None
    default_model_name: str
    fast_default_model_name: Optional[str] = None
    deployment_name: Optional[str] = None
    default_vision_model: Optional[str] = None
    model_configurations: Optional[List[Dict[str, Any]]] = None  # 字典列表，便于序列化
    category: str = 'general'
    is_default_provider: bool = False
    is_default_vision_provider: bool = False



