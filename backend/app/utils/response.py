from fastapi import HTTPException
from app.schemas.common import ApiResponse
from typing import Optional, Any

def error_response(message: str, data: Optional[Any] = None) -> ApiResponse:
    """创建统一错误响应"""
    return ApiResponse(
        success=False,
        code=-1,
        message=message,
        data=data
    )

def success_response(message: str = "success", data: Optional[Any] = None) -> ApiResponse:
    """创建统一成功响应"""
    return ApiResponse(
        success=True,
        code=0,
        message=message,
        data=data
    )

def not_found_error(resource_name: str) -> ApiResponse:
    """创建资源未找到错误响应"""
    return error_response(f"{resource_name} not found")

def validation_error(message: str) -> ApiResponse:
    """创建验证错误响应"""
    return error_response(f"参数验证失败: {message}")
