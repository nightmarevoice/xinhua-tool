from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func
from app.database.database import Base

class Prompt(Base):
    """Prompt 配置存储模型"""
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, nullable=True, index=True)  # backend 系统的 ID
    title = Column(String(200), nullable=False)
    system_prompt = Column(Text, nullable=True)  # 系统提示词
    user_prompt = Column(Text, nullable=True)  # 用户提示词
    model_type = Column(String(50), nullable=False)  # proprietary, general
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())