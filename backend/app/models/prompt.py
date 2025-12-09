from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    system_prompt = Column(Text, nullable=True)  # 系统提示词
    user_prompt = Column(Text, nullable=True)  # 用户提示词
    model_type = Column(String(50), nullable=False)  # proprietary, general
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
