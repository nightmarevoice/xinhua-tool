from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Text
from sqlalchemy.sql import func
from app.database import Base

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    call_time = Column(DateTime(timezone=True), server_default=func.now(), comment="调用时间")
    
    # 基础参数
    input_params = Column(JSON, comment="传入的参数")
    
    # 专有模型相关
    proprietary_params = Column(JSON, nullable=True, comment="专有模型参数")
    proprietary_response = Column(Text, nullable=True, comment="专有模型的返回值")
    
    # 通用模型相关
    general_params = Column(JSON, nullable=True, comment="通用模型参数")
    general_response = Column(Text, nullable=True, comment="通用模型的返回值")
    
    # 耗时
    duration = Column(Float, comment="调用接口到返回消耗的时间(秒)")
