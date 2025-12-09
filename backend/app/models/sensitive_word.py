from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class SensitiveWordGroup(Base):
    __tablename__ = "sensitive_word_groups"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    words = Column(JSON, nullable=False)  # 存储敏感词列表
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())












