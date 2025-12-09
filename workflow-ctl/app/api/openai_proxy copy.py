import os
import json
import httpx
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- 配置 ---
LOG_FILE = "proxy.log"

# 日志配置 (保持不变)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 核心代理配置 (保持不变)
VLLM_HOST = os.getenv("VLLM_HOST", "127.0.0.1")
VLLM_PORT = int(os.getenv("VLLM_PORT", 8002))
VLLM_BASE_URL = f"http://{VLLM_HOST}:{VLLM_PORT}"
API_KEY = "xuanfeng_sdfasdfsdfkkllli8i3"

# --- [新增] 风控模型服务地址 ---
RISK_CONTROL_URL = os.getenv("RISK_CONTROL_URL", "http://127.0.0.1:6008/censor")

# --- [新增] 模型参数控制 --- 
# Temperature 控制 (0.0 - 2.0, 越小越确定, 越大越随机)
DEFAULT_TEMPERATURE = 0.7
MAX_TEMPERATURE = 1.2

# Max Tokens 控制 (输出的最大长度)
DEFAULT_MAX_TOKENS = 1024
MAX_MAX_TOKENS = 4096
# ---------------------------------

# 应用生命周期管理 (保持不变)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时创建 HTTP 客户端，关闭时清理资源"""
    app.state.client = httpx.AsyncClient(
        timeout=None,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=50,
            keepalive_expiry=30.0
        )
    )
    logger.info("HTTP 客户端已初始化，支持高并发连接")
    yield
    await app.state.client.aclose()
    logger.info("HTTP 客户端已关闭")

app = FastAPI(lifespan=lifespan)
auth_scheme = HTTPBearer()

# API Key 验证 (保持不变)
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    if credentials.scheme.lower() != "bearer" or credentials.credentials != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return credentials

# --- [修改] 风险控制模块 ---
async def check_content_safety(request_data: dict, client: httpx.AsyncClient):
    """通过调用外部风控 API 检查内容安全。"""
    full_prompt = "".join(
        str(msg.get("content", "")) for msg in request_data.get("messages", []) if isinstance(msg, dict))
    if not full_prompt.strip():
        return False, None  # 如果没有内容，视为安全

    try:
        # 调用风控模型服务
        response = await client.post(RISK_CONTROL_URL, json={"text": full_prompt}, timeout=5.0)
        response.raise_for_status()
        result = response.json()

        # 如果模型返回 "is_safe" 为 False，则判定为不安全
        if not result.get("is_safe", True):
            label = result.get("label", "unknown_risk")
            logger.warning(f"检测到风险内容，风控模型标签: '{label}'")
            return True, f"请求内容被风控模型识别为不安全 (标签: {label})"

        return False, None  # 安全

    except httpx.RequestError as e:
        logger.error(f"调用风控服务失败: {e}")
        # 安全策略：当风控服务不可用时，拒绝请求
        return True, "无法连接到内容安全审查服务"
    except Exception as e:
        logger.error(f"解析风控服务响应时发生未知错误: {e}")
        return True, "内容安全审查服务返回无效响应"
# -----------------------------

@app.get("/v1/logs", response_class=PlainTextResponse, dependencies=[Depends(verify_api_key)])
async def get_logs(lines: int = 50):
    """安全地获取最新的 N 行日志"""
    if not os.path.exists(LOG_FILE):
        return "日志文件不存在。"
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
            last_lines = log_lines[-lines:]
            return "".join(last_lines)
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")
        raise HTTPException(status_code=500, detail="无法读取日志文件。")

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def proxy_chat_completions(request: Request):
    """代理 chat completions 请求"""
    return await proxy_to_vllm(request, "chat/completions")

async def proxy_to_vllm(request: Request, path: str):
    """将请求代理到 vLLM 服务器的核心逻辑"""
    client = request.app.state.client
    target_url = f"{VLLM_BASE_URL}/v1/{path}"
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        request_data = json.loads(body.decode('utf-8'))
        is_streaming = request_data.get("stream", False)
    except Exception:
        request_data = {}
        is_streaming = False

    # --- [插入] 调用安全检查 ---
    is_unsafe, reason = await check_content_safety(request_data, client)
    if is_unsafe:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": {
                "message": f"您的请求因内容安全问题被拒绝: {reason}",
                "type": "content_policy_violation",
                "code": "content_policy_violation"
            }}
        )

    # --- [新增] 参数检查与强制应用 ---
    # 处理 temperature
    temp = request_data.get('temperature')
    if temp is None:
        request_data['temperature'] = DEFAULT_TEMPERATURE
        logger.info(f"请求未提供 temperature，应用默认值: {DEFAULT_TEMPERATURE}")
    elif temp > MAX_TEMPERATURE:
        request_data['temperature'] = MAX_TEMPERATURE
        logger.warning(f"客户端 temperature ({temp}) 超出最大值，强制设为: {MAX_TEMPERATURE}")

    # 处理 max_tokens
    max_toks = request_data.get('max_tokens')
    if max_toks is None:
        request_data['max_tokens'] = DEFAULT_MAX_TOKENS
        logger.info(f"请求未提供 max_tokens，应用默认值: {DEFAULT_MAX_TOKENS}")
    elif max_toks > MAX_MAX_TOKENS:
        request_data['max_tokens'] = MAX_MAX_TOKENS
        logger.warning(f"客户端 max_tokens ({max_toks}) 超出最大值，强制设为: {MAX_MAX_TOKENS}")
    
    # 将修改后的数据重新编码为请求体
    body = json.dumps(request_data).encode('utf-8')
    # ---------------------------------

    # -----------------------------
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": {
                "message": f"您的请求因内容安全问题被拒绝: {reason}",
                "type": "content_policy_violation",
                "code": "content_policy_violation"
            }}
        )
    # -----------------------------

    try:
        vllm_req = client.build_request(method=request.method, url=target_url, headers=headers, content=body)
        vllm_response = await client.send(vllm_req, stream=True)

        if is_streaming:
            response_headers = dict(vllm_response.headers)
            response_headers["Content-Type"] = "text/event-stream; charset=utf-8"
            return StreamingResponse(vllm_response.aiter_bytes(), status_code=vllm_response.status_code,
                                     headers=response_headers)
        else:
            response_body = await vllm_response.aread()
            await vllm_response.aclose()
            response_json = json.loads(response_body)

            usage = response_json.get("usage")
            if usage:
                logger.info(f"非流式请求完成 - Tokens: {usage.get('total_tokens', 0)}")
            return JSONResponse(content=response_json, status_code=vllm_response.status_code)

    except httpx.ConnectError as e:
        logger.error(f"连接 vLLM 失败: {e}")
        return JSONResponse(status_code=502,
                            content={"error": "Proxy failed to connect to VLLM service.", "details": str(e)})
    except Exception as e:
        logger.error(f"代理时发生未知错误: {e}", exc_info=True)
        return JSONResponse(status_code=500,
                            content={"error": "An unexpected error occurred in the proxy.", "details": str(e)})

# Uvicorn 启动配置 (保持不变)
if __name__ == "__main__":
    import uvicorn
    # 确保文件名是 openai_proxy.py
    uvicorn.run(
        "openai_proxy:app",
        host="0.0.0.0",
        port=6006,
        workers=8,
        limit_concurrency=100,
        timeout_keep_alive=30
    )