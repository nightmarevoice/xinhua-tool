from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer
from sqlalchemy.sql import func
from app.database import Base

class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # openai, azure, anthropic, google, custom
    api_key = Column(String(500), nullable=True)
    api_base = Column(String(500), nullable=True)
    api_version = Column(String(50), nullable=True)
    custom_config = Column(JSON, nullable=True)
    default_model_name = Column(String(100), nullable=False)
    fast_default_model_name = Column(String(100), nullable=True)
    deployment_name = Column(String(100), nullable=True)
    default_vision_model = Column(String(100), nullable=True)
    model_configurations = Column(JSON, nullable=True)  # 存储模型配置数组
    category = Column(String(20), nullable=False, default='general')  # general, professional
    is_default_provider = Column(Boolean, default=False)
    is_default_vision_provider = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
