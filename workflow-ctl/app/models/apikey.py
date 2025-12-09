from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func
from app.database.database import Base

class ApiKey(Base):
    """API Key 存储模型"""
    __tablename__ = "apikeys"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, nullable=True, index=True)  # backend 系统的 ID
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(20), default="active")  # active, inactive
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

