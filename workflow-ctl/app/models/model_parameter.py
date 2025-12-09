from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Boolean
from sqlalchemy.sql import func
from app.database.database import Base

class ModelParameter(Base):
    """模型参数配置存储模型"""
    __tablename__ = "model_parameters"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, nullable=True, index=True)  # backend 系统的 ID
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # string, number, boolean, array, object
    default_value = Column(JSON)
    model_type = Column(String(50), nullable=False)  # proprietary, general
    description = Column(Text, nullable=False)
    required = Column(Boolean, default=False)
    validation = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


