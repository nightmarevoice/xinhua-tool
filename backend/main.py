from fastapi import FastAPI, Request, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api import apikey, workflow, prompt, model_parameter, llm_provider, model_chat, chat, sensitive_word, chat_log
from app.api import proxy as proxy_router
from app.api import reverse_proxy
from app.database import engine, Base, get_db
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    starlette_http_exception_handler,
    general_exception_handler
)
from sqlalchemy.orm import Session
from typing import Optional
import os
import time
from dotenv import load_dotenv

load_dotenv()

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Admin Manage System API",
    description="管理后台系统 API",
    version="1.0.0",
    docs_url=None,  # 禁用默认文档
    redoc_url=None,  # 禁用默认文档
    openapi_url="/openapi.json",
    redirect_slashes=False  # 禁用自动重定向斜杠
)

# 配置CORS
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:9000", 
    "http://127.0.0.1:3000",
    "http://127.0.0.1:9000",
    "http://localhost:5173",  # Vite默认端口
    "http://127.0.0.1:5173"
]

# 从环境变量读取额外的允许源
env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins:
    allowed_origins.extend(env_origins.split(","))

# 添加CORS中间件 - 必须在路由注册之前
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600,
)

# 自定义Swagger UI路由，使用国内可访问的CDN
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@2.0.0/bundles/redoc.standalone.js",
    )

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求的中间件"""
    start_time = time.time()
    
    # 记录请求信息
    print(f"🔍 请求: {request.method} {request.url}")
    print(f"🔍 来源: {request.headers.get('origin', 'Unknown')}")
    print(f"🔍 用户代理: {request.headers.get('user-agent', 'Unknown')}")
    
    # 特别关注apikeys请求
    if 'apikeys' in str(request.url):
        print(f"🚨 特别关注: apikeys请求 - {request.method} {request.url}")
        print(f"🚨 请求头: {dict(request.headers)}")
    
    response = await call_next(request)
    
    # 记录响应信息
    process_time = time.time() - start_time
    print(f"✅ 响应: {response.status_code} - 耗时: {process_time:.3f}s")
    
    # 特别关注apikeys响应
    if 'apikeys' in str(request.url):
        print(f"🚨 apikeys响应: {response.status_code}")
        print(f"🚨 响应头: {dict(response.headers)}")
    
    return response

# 添加全局异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 添加全局OPTIONS处理器
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """处理所有OPTIONS预检请求"""
    print(f"OPTIONS请求: {full_path}")
    return {"message": "OK"}

# 注册路由
print("注册路由...")
app.include_router(apikey.router, prefix="/api/apikeys", tags=["API Key管理"])
print("apikey路由注册完成")

# 注意：不需要额外的路由处理，因为FastAPI会自动处理带斜杠和不带斜杠的请求

app.include_router(workflow.router, prefix="/api/workflows", tags=["流程配置"])
print("workflow路由注册完成")
app.include_router(prompt.router, prefix="/api/prompts", tags=["Prompt配置"])
print("prompt路由注册完成")
app.include_router(model_parameter.router, prefix="/api/model-parameters", tags=["模型参数配置"])
print("model_parameter路由注册完成")
app.include_router(llm_provider.router, prefix="/api/llm-providers", tags=["LLM Provider配置"])
print("llm_provider路由注册完成")
app.include_router(model_chat.router, prefix="/api/model-chat", tags=["模型对话"])
print("model_chat路由注册完成")
app.include_router(chat.router, prefix="/api/chat", tags=["流式聊天"])
print("chat路由注册完成")
app.include_router(sensitive_word.router, prefix="/api/sensitive-words", tags=["敏感词配置"])
print("sensitive_word路由注册完成")
app.include_router(proxy_router.router, prefix="/proxy", tags=["反向代理"])
print("proxy路由注册完成")

# Reverse proxy for embedding Alethea
app.include_router(reverse_proxy.router, prefix="/proxy/alethea", tags=["Reverse Proxy"])
print("reverse_proxy路由注册完成")

app.include_router(chat_log.router, prefix="/api/chat-logs", tags=["聊天日志"])
print("chat_log路由注册完成")

@app.get("/")
async def root():
    return {"message": "Admin Manage System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
