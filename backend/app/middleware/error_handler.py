from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    """统一处理HTTP异常，返回相应的状态码和统一错误格式"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": -1,
            "message": exc.detail,
            "data": None
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常"""
    logger.error(f"请求验证异常: {exc.errors()}")
    
    # 提取第一个验证错误信息
    error_msg = "请求参数验证失败"
    if exc.errors():
        first_error = exc.errors()[0]
        field = first_error.get('loc', ['unknown'])[-1]
        error_detail = first_error.get('msg', '参数错误')
        error_msg = f"{field}: {error_detail}"
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": -1,
            "message": error_msg,
            "data": None
        }
    )

async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理Starlette HTTP异常"""
    logger.error(f"Starlette HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": -1,
            "message": exc.detail,
            "data": None
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """处理其他未捕获的异常"""
    logger.error(f"未捕获异常: {type(exc).__name__} - {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": -1,
            "message": "服务器内部错误",
            "data": None
        }
    )
