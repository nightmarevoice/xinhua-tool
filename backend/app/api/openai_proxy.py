import os
import json
import httpx
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- 配置 ---
# 日志文件路径：基于当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "proxy.log")

# 配置日志记录到文件和控制台
# 移除所有现有的处理器
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'),  # 明确指定 UTF-8 编码
        logging.StreamHandler()  # 同时打印到控制台
    ]
)
logger = logging.getLogger(__name__)

VLLM_HOST = os.getenv("VLLM_HOST", "118.196.43.238")
VLLM_PORT = int(os.getenv("VLLM_PORT", 8002))
VLLM_BASE_URL = f"http://{VLLM_HOST}:{VLLM_PORT}"
API_KEY = "xuanfeng_sdfasdfsdfkkllli8i3"
# --- 结束配置 ---

app = FastAPI()
client = httpx.AsyncClient(timeout=None)
auth_scheme = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """依赖项：验证 API 密钥"""
    if credentials.scheme.lower() != "bearer" or credentials.credentials != API_KEY:
        logger.warning(f"无效的 API Key: {credentials.credentials}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    # 认证成功后不再打印日志，避免日志刷屏
    return credentials


@app.get("/v1/logs", response_class=PlainTextResponse, dependencies=[Depends(verify_api_key)])
async def get_logs(lines: int = 50):
    """安全地获取最新的 N 行日志"""
    if not os.path.exists(LOG_FILE):
        return "日志文件不存在。"
    try:
        # 尝试多种编码方式读取日志文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
        log_lines = None
        
        for encoding in encodings:
            try:
                with open(LOG_FILE, 'r', encoding=encoding, errors='replace') as f:
                    log_lines = f.readlines()
                    break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if log_lines is None:
            # 如果所有编码都失败，使用二进制模式读取并尝试解码
            with open(LOG_FILE, 'rb') as f:
                content = f.read()
                # 尝试UTF-8解码，忽略错误
                log_lines = content.decode('utf-8', errors='replace').splitlines(keepends=True)
        
        # 读取所有行，然后取最后 N 行
        last_lines = log_lines[-lines:]
        return "".join(last_lines)
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="无法读取日志文件。")


@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def proxy_chat_completions(request: Request):
    """代理 chat completions 请求"""
    return await proxy_to_vllm(request, "chat/completions")


async def proxy_to_vllm(request: Request, path: str):
    """将请求代理到 vLLM 服务器的核心逻辑"""
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

    try:
        vllm_req = client.build_request(
            method=request.method, url=target_url, headers=headers, content=body
        )
        vllm_response = await client.send(vllm_req, stream=True)

        if is_streaming:
            response_headers = dict(vllm_response.headers)
            response_headers["Content-Type"] = "text/event-stream; charset=utf-8"
            return StreamingResponse(
                stream_response_generator(vllm_response, request_data),
                status_code=vllm_response.status_code,
                headers=response_headers,
            )
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


async def stream_response_generator(vllm_response, request_data):
    """用于流式响应的异步生成器"""
    full_response_content = ""
    try:
        async for chunk in vllm_response.aiter_bytes():
            full_response_content += chunk.decode('utf-8', errors='ignore')
            yield chunk
    finally:
        await vllm_response.aclose()
        logger.info("vLLM 流式连接已关闭")

    # ... (usage 解析逻辑保持不变)
    try:
        final_data = {}
        lines = full_response_content.strip().split('\n\n')
        for line in reversed(lines):
            if line.startswith("data: "):
                content = line[len("data: "):].strip()
                if content and content != "[DONE]":
                    final_data = json.loads(content)
                    break
        usage = final_data.get("usage")
        if usage:
            logger.info(f"流式请求完成 - Tokens: {usage.get('total_tokens', 0)}")
    except Exception as e:
        logger.error(f"解析流式响应的 usage 失败: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6006)