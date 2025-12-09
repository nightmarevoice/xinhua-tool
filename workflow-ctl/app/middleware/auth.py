from fastapi import HTTPException, Request, status, Depends, Header
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.apikey import ApiKey
from typing import Optional

def verify_api_key(request: Request, db: Session) -> bool:
    """
    验证 API Key（用于中间件）
    从请求头中获取 Authorization，并验证是否存在于数据库中
    """
    # 获取 Authorization header
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    # 提取 API Key (Bearer <key> 或直接 <key>)
    if authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "")
    elif authorization.startswith("ApiKey "):
        api_key = authorization.replace("ApiKey ", "")
    else:
        api_key = authorization
    
    # 查询数据库中是否存在该 API Key
    db_key = db.query(ApiKey).filter(
        ApiKey.key == api_key,
        ApiKey.status == "active"
    ).first()
    
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    return True


def get_api_key_from_header(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> str:
    """
    从请求头中提取 API Key
    支持格式：Bearer <key>, ApiKey <key>, 或直接 <key>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    # 提取 API Key
    if authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "").strip()
    elif authorization.startswith("ApiKey "):
        return authorization.replace("ApiKey ", "").strip()
    else:
        return authorization.strip()


def verify_api_key_dependency(
    api_key: str = Depends(get_api_key_from_header),
    db: Session = Depends(get_db)
) -> ApiKey:
    """
    FastAPI 依赖函数：验证 API Key
    在所有需要认证的路由上使用：Depends(verify_api_key_dependency)
    
    返回验证通过的 ApiKey 对象，如果验证失败则抛出 HTTPException
    """
    # 查询数据库中是否存在该 API Key 且状态为 active
    db_key = db.query(ApiKey).filter(
        ApiKey.key == api_key,
        ApiKey.status == "active"
    ).first()
    
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key"
        )
    
    return db_key


async def auth_middleware(request: Request, call_next):
    """
    网关认证中间件
    对所有请求进行 API Key 验证（除了健康检查和文档路径）
    """
    # 跳过健康检查和文档的认证
    skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    
    # 如果路径需要跳过认证
    if request.url.path in skip_paths or request.url.path.startswith("/api/auth"):
        return await call_next(request)
    
    # 对于所有其他路径，需要认证
    db = next(get_db())
    try:
        verify_api_key(request, db)
        return await call_next(request)
    except HTTPException:
        db.close()
        raise
    finally:
        db.close()








