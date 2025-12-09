from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色: user, assistant, system")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="温度参数")
    provider_id: Optional[int] = Field(None, description="LLM Provider ID")

class SimpleChatRequest(BaseModel):
    """简单聊天请求模型"""
    prompt: str = Field(..., description="用户输入")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="温度参数")
    provider_id: Optional[int] = Field(None, description="LLM Provider ID")

class ModelUsage(BaseModel):
    """模型使用统计"""
    prompt_tokens: int = Field(0, description="输入token数量")
    completion_tokens: int = Field(0, description="输出token数量")
    total_tokens: int = Field(0, description="总token数量")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    content: str = Field(..., description="模型回复内容")
    model: str = Field(..., description="使用的模型名称")
    usage: Optional[ModelUsage] = Field(None, description="使用统计")
    timestamp: str = Field(..., description="响应时间戳")

class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型ID")
    object: str = Field(..., description="对象类型")
    created: int = Field(..., description="创建时间")
    owned_by: str = Field(..., description="拥有者")

class ModelsListResponse(BaseModel):
    """模型列表响应"""
    models: List[ModelInfo] = Field(..., description="模型列表")
    total: int = Field(..., description="模型总数")

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    model: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API基础URL")
    test_response: str = Field(..., description="测试响应")



