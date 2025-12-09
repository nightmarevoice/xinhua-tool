from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Union
import logging
import httpx
from pydantic import BaseModel

from app.database.database import get_db
from app.models.apikey import ApiKey
from app.middleware.auth import verify_api_key_dependency
from app.schemas.common import Response
from app.config import FORBIDDEN_WORDS_URL, FORBIDDEN_WORDS_API_KEY

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 请求模型 ====================

class AddWordRequest(BaseModel):
    """添加违禁词请求模型"""
    word: Optional[str] = None
    words: Optional[List[str]] = None


class DeleteWordRequest(BaseModel):
    """删除违禁词请求模型"""
    word: Optional[str] = None
    words: Optional[List[str]] = None


# ==================== 违禁词管理接口 ====================

@router.post("/add", response_model=Response)
async def add_forbidden_words(
    request: AddWordRequest = Body(...),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    添加违禁词
    调用外部服务 POST /v1/forbidden-words
    
    请求体:
    - {"word": "违禁词"} 或
    - {"words": ["词1", "词2", "词3"]}
    """
    try:
        # 验证请求参数
        if not request.word and not request.words:
            raise HTTPException(
                status_code=400,
                detail="必须提供 word 或 words 参数"
            )
        
        if request.word and request.words:
            raise HTTPException(
                status_code=400,
                detail="不能同时提供 word 和 words 参数"
            )
        
        # 构建请求数据
        request_data = {}
        if request.word:
            request_data["word"] = request.word
            logger.info(f"准备添加违禁词: {request.word}")
        else:
            request_data["words"] = request.words
            logger.info(f"准备批量添加违禁词: {len(request.words)} 个")
        
        # 调用外部服务
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                FORBIDDEN_WORDS_URL,
                headers={
                    "Authorization": f"Bearer {FORBIDDEN_WORDS_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"外部服务返回错误: status={response.status_code}, body={response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"添加违禁词失败: {response.text}"
                )
            
            # 解析响应
            result = response.json()
            logger.info(f"添加违禁词成功: {result}")
            
            return Response(
                success=True,
                message="添加违禁词成功",
                data=result
            )
            
    except httpx.RequestError as e:
        logger.error(f"调用外部服务失败: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"无法连接到违禁词服务: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加违禁词失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"添加违禁词失败: {str(e)}"
        )


@router.delete("/delete", response_model=Response)
async def delete_forbidden_words(
    request: DeleteWordRequest = Body(...),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    删除违禁词
    调用外部服务 DELETE /v1/forbidden-words
    
    请求体:
    - {"word": "违禁词"} 或
    - {"words": ["词1", "词2"]}
    """
    try:
        # 验证请求参数
        if not request.word and not request.words:
            raise HTTPException(
                status_code=400,
                detail="必须提供 word 或 words 参数"
            )
        
        if request.word and request.words:
            raise HTTPException(
                status_code=400,
                detail="不能同时提供 word 和 words 参数"
            )
        
        # 构建请求数据
        request_data = {}
        if request.word:
            request_data["word"] = request.word
            logger.info(f"准备删除违禁词: {request.word}")
        else:
            request_data["words"] = request.words
            logger.info(f"准备批量删除违禁词: {len(request.words)} 个")
        
        # 调用外部服务
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method="DELETE",
                url=FORBIDDEN_WORDS_URL,
                headers={
                    "Authorization": f"Bearer {FORBIDDEN_WORDS_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"外部服务返回错误: status={response.status_code}, body={response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"删除违禁词失败: {response.text}"
                )
            
            # 解析响应
            result = response.json()
            logger.info(f"删除违禁词成功: {result}")
            
            return Response(
                success=True,
                message="删除违禁词成功",
                data=result
            )
            
    except httpx.RequestError as e:
        logger.error(f"调用外部服务失败: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"无法连接到违禁词服务: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除违禁词失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除违禁词失败: {str(e)}"
        )


@router.get("/list", response_model=Response)
async def get_forbidden_words_list():
    """
    获取违禁词列表
    调用外部服务 GET /v1/forbidden-words
    
    注意: 此接口不需要 API Key 认证
    """
    try:
        logger.info("准备获取违禁词列表")
        
        # 调用外部服务
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                FORBIDDEN_WORDS_URL,
                headers={
                    "Authorization": f"Bearer {FORBIDDEN_WORDS_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"外部服务返回错误: status={response.status_code}, body={response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"获取违禁词列表失败: {response.text}"
                )
            
            # 解析响应
            result = response.json()
            logger.info(f"获取违禁词列表成功: 共 {len(result.get('words', []))} 个违禁词")
            
            return Response(
                success=True,
                message="获取违禁词列表成功",
                data=result
            )
            
    except httpx.RequestError as e:
        logger.error(f"调用外部服务失败: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"无法连接到违禁词服务: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取违禁词列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取违禁词列表失败: {str(e)}"
        )

