from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import openai
import os
from datetime import datetime

from app.database import get_db
from app.models.llm_provider import LLMProvider as LLMProviderModel
from app.schemas.common import ApiResponse
from app.schemas.model_chat import ChatRequest, SimpleChatRequest, ChatResponse, ModelsListResponse, HealthCheckResponse, ChatMessage
from app.utils.response import error_response, success_response, not_found_error

router = APIRouter()

# RunPod配置
RUNPOD_URL = "https://kvqp6oecjzde3a-64410d4a-8888.proxy.runpod.net/v1"
MODEL_NAME = "Qwen/Qwen1.5-7B-Chat-GPTQ-Int4"  # 默认模型名称

@router.post("/chat", response_model=ApiResponse)
async def chat_with_model(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    与模型进行对话
    
    Args:
        request: 聊天请求对象，包含messages, model, temperature, provider_id
    """
    try:
        # 获取模型配置
        model_name = request.model or MODEL_NAME
        api_base = RUNPOD_URL
        api_key = "EMPTY"
        
        # 如果指定了provider_id，从数据库获取配置
        if request.provider_id:
            provider = db.query(LLMProviderModel).filter(LLMProviderModel.id == request.provider_id).first()
            if provider:
                if provider.api_base:
                    api_base = provider.api_base
                if provider.api_key:
                    api_key = provider.api_key
                if provider.default_model_name:
                    model_name = provider.default_model_name
        
        # 创建OpenAI客户端
        client = openai.OpenAI(
            base_url=api_base,
            api_key=api_key
        )
        
        # 调用模型
        chat_response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            temperature=request.temperature,
        )
        
        # 提取响应内容
        content = chat_response.choices[0].message.content
        usage = {
            "prompt_tokens": chat_response.usage.prompt_tokens if chat_response.usage else 0,
            "completion_tokens": chat_response.usage.completion_tokens if chat_response.usage else 0,
            "total_tokens": chat_response.usage.total_tokens if chat_response.usage else 0
        }
        
        response_data = {
            "content": content,
            "model": model_name,
            "usage": usage,
            "timestamp": datetime.now().isoformat()
        }
        
        return success_response("模型调用成功", response_data)
        
    except openai.APIError as e:
        return error_response(f"OpenAI API错误: {str(e)}")
    except Exception as e:
        return error_response(f"模型调用失败: {str(e)}")

@router.post("/chat/simple", response_model=ApiResponse)
async def simple_chat(
    request: SimpleChatRequest,
    db: Session = Depends(get_db)
):
    """
    简单对话接口
    
    Args:
        request: 简单聊天请求对象，包含prompt, model, temperature, provider_id
    """
    try:
        # 构建消息
        messages = [
            ChatMessage(role="system", content="You are a helpful AI assistant"),
            ChatMessage(role="user", content=request.prompt)
        ]
        
        # 使用字典创建请求，然后在函数内部转换为模型
        chat_request = ChatRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature
        )
        # 手动设置 provider_id
        chat_request.provider_id = request.provider_id
        
        # 调用chat接口
        return await chat_with_model(chat_request, db)
        
    except Exception as e:
        return error_response(f"简单对话失败: {str(e)}")

@router.get("/models", response_model=ApiResponse)
async def get_available_models():
    """
    获取可用的模型列表
    """
    try:
        # 创建客户端
        client = openai.OpenAI(
            base_url=RUNPOD_URL,
            api_key="EMPTY"
        )
        
        # 获取模型列表
        models = client.models.list()
        
        model_list = []
        for model in models.data:
            model_list.append({
                "id": model.id,
                "object": model.object,
                "created": model.created,
                "owned_by": getattr(model, 'owned_by', 'unknown')
            })
        
        return success_response("获取模型列表成功", {
            "models": model_list,
            "total": len(model_list)
        })
        
    except Exception as e:
        return error_response(f"获取模型列表失败: {str(e)}")

@router.get("/health", response_model=ApiResponse)
async def check_model_health():
    """
    检查模型服务健康状态
    """
    try:
        # 创建客户端
        client = openai.OpenAI(
            base_url=RUNPOD_URL,
            api_key="EMPTY"
        )
        
        # 发送测试请求
        test_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0,
            max_tokens=10
        )
        
        return success_response("模型服务正常", {
            "status": "healthy",
            "model": MODEL_NAME,
            "base_url": RUNPOD_URL,
            "test_response": test_response.choices[0].message.content
        })
        
    except Exception as e:
        return error_response(f"模型服务异常: {str(e)}")
