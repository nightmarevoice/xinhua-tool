from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict, List
from datetime import datetime

class ModelConfiguration(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    name: str
    max_input_tokens: int
    supports_function_calling: bool

class LLMProviderBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
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

class LLMProviderCreate(LLMProviderBase):
    pass

class LLMProviderUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    custom_config: Optional[Dict[str, str]] = None
    default_model_name: Optional[str] = None
    fast_default_model_name: Optional[str] = None
    deployment_name: Optional[str] = None
    default_vision_model: Optional[str] = None
    model_configurations: Optional[List[ModelConfiguration]] = None
    category: Optional[str] = None
    is_default_provider: Optional[bool] = None
    is_default_vision_provider: Optional[bool] = None

class LLMProvider(LLMProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
