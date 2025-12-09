from sqlalchemy import Column, String, DateTime, Text, Integer, JSON
from sqlalchemy.sql import func
from app.database.database import Base

class Workflow(Base):
    """流程配置存储模型"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, nullable=True, index=True)  # backend 系统的 ID（哈希值）
    backend_id = Column(String(36), nullable=True, index=True)  # backend 系统的原始字符串 ID（UUID）
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(String(50), nullable=False)  # proprietary, general, etc.
    config = Column(JSON, nullable=False)  # 存储完整的流程配置
    status = Column(String(20), default="active", nullable=False)  # active, inactive
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

