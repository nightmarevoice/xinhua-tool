from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.database.database import engine, Base, get_db
from app.api import apikey, workflow, prompt, model_parameter, llm_provider, chat, sensitive_word
from app.middleware.auth import auth_middleware
import time

# 加载环境变量
load_dotenv()

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Workflow Control API",
    description="工作流控制服务 - 提供 API Key 认证和配置存储",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:9000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:9000",
    "http://192.168.1.7:3000",  # 添加局域网访问支持
    "http://192.168.1.7:9000",  # 添加局域网访问支持
]

# 从环境变量读取额外的允许源
env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins:
    allowed_origins.extend(env_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，便于开发和测试
    allow_credentials=False,  # 允许所有源时需要设置为 False
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求的中间件"""
    start_time = time.time()
    
    print(f"🔍 请求: {request.method} {request.url}")
    print(f"🔍 来源: {request.headers.get('origin', 'Unknown')}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"✅ 响应: {response.status_code} - 耗时: {process_time:.3f}s")
    
    return response

# 注意：认证中间件应该在其他中间件之后添加，但在路由之前
# 但是 FastAPI 的 middleware 是在所有请求处理之前执行的
# 所以我们需要直接在路由层面添加认证依赖

# 注册路由（API Key 管理不需要认证）
app.include_router(apikey.router, prefix="/api/apikeys", tags=["API Key 管理"])

# 以下路由都需要认证（通过依赖注入）
app.include_router(workflow.router, prefix="/api/workflows", tags=["流程配置"])
app.include_router(prompt.router, prefix="/api/prompts", tags=["Prompt 配置"])
app.include_router(model_parameter.router, prefix="/api/model-parameters", tags=["模型参数配置"])
app.include_router(llm_provider.router, prefix="/api/llm-providers", tags=["LLM Provider 配置"])
app.include_router(chat.router, prefix="/api/chat", tags=["流式聊天"])
app.include_router(sensitive_word.router, prefix="/api/sensitive-words", tags=["违禁词管理"])

@app.get("/")
async def root():
    return {"message": "Workflow Control Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8889))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)






