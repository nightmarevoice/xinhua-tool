from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class ApiKey(Base):
    __tablename__ = "apikeys"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    key = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(20), default="active")  # active, inactive
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
