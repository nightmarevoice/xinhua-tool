from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import secrets
import logging
from datetime import datetime

from app.database import get_db
from app.models.apikey import ApiKey as ApiKeyModel
from app.schemas.apikey import ApiKey, ApiKeyCreate, ApiKeyUpdate
from app.schemas.common import PaginatedResponse, ApiResponse
from app.utils.response import error_response, success_response, not_found_error
from app.utils.workflow_ctl_sync import sync_apikey_to_workflow_ctl, delete_from_workflow_ctl, clear_apikey_cache

router = APIRouter()
logger = logging.getLogger(__name__)

def generate_api_key():
    """生成API Key"""
    return f"ak_{secrets.token_urlsafe(32)}"

@router.get("/list", response_model=PaginatedResponse[ApiKey])
async def get_apikeys(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取API Key列表"""
    query = db.query(ApiKeyModel)
    
    if search:
        query = query.filter(
            ApiKeyModel.name.contains(search) | 
            ApiKeyModel.description.contains(search)
        )
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 将SQLAlchemy模型转换为Pydantic模型
    api_key_items = [ApiKey.from_orm(item) for item in items]
    
    from app.schemas.common import PaginatedData
    
    return PaginatedResponse[ApiKey](
        data=PaginatedData[ApiKey](
            items=api_key_items,
            total=total,
            page=page,
            page_size=page_size
        )
    )

@router.get("/get", response_model=ApiResponse[ApiKey])
async def get_apikey(apikey_id: str = Query(..., description="API Key ID"), db: Session = Depends(get_db)):
    """获取单个API Key"""
    apikey = db.query(ApiKeyModel).filter(ApiKeyModel.id == apikey_id).first()
    if not apikey:
        return not_found_error("API Key")
    
    return success_response("获取API Key成功", ApiKey.from_orm(apikey))

@router.post("/create", response_model=ApiResponse[ApiKey])
async def create_apikey(apikey: ApiKeyCreate, db: Session = Depends(get_db)):
    """创建API Key"""
    # 检查名称是否已存在
    existing_apikey = db.query(ApiKeyModel).filter(ApiKeyModel.name == apikey.name).first()
    if existing_apikey:
        return error_response("API Key名称已存在，请使用不同的名称")
    
    # 生成新的API Key
    api_key_value = generate_api_key()
    
    db_apikey = ApiKeyModel(
        id=str(uuid.uuid4()),
        name=apikey.name,
        description=apikey.description,
        key=api_key_value,
        status="active"
    )
    
    db.add(db_apikey)
    db.commit()
    db.refresh(db_apikey)
    
    # 清除 API Key 缓存，确保新创建的 API Key 可以被使用
    clear_apikey_cache()
    
    # 同步到 workflow-ctl（失败不影响主流程）
    try:
        sync_success = await sync_apikey_to_workflow_ctl(
            external_id=db_apikey.id,
            name=db_apikey.name,
            description=db_apikey.description,
            key=db_apikey.key,
            status=db_apikey.status
        )
        if not sync_success:
            logger.warning(f"API Key 创建成功，但同步到 workflow-ctl 失败: id={db_apikey.id}")
    except Exception as e:
        # 同步失败不影响主流程，只记录日志
        logger.error(f"API Key 创建成功，但同步到 workflow-ctl 时发生异常: id={db_apikey.id}, error={str(e)}")
    
    return success_response("API Key创建成功", ApiKey.from_orm(db_apikey))

@router.put("/update", response_model=ApiResponse[ApiKey])
async def update_apikey(
    apikey_id: str = Query(..., description="API Key ID"),
    apikey: ApiKeyUpdate = None,
    db: Session = Depends(get_db)
):
    """更新API Key"""
    db_apikey = db.query(ApiKeyModel).filter(ApiKeyModel.id == apikey_id).first()
    if not db_apikey:
        return not_found_error("API Key")
    
    if apikey:
        update_data = apikey.model_dump(exclude_unset=True)
        
        # 如果更新名称，检查名称是否已存在（排除当前记录）
        if 'name' in update_data:
            existing_apikey = db.query(ApiKeyModel).filter(
                ApiKeyModel.name == update_data['name'],
                ApiKeyModel.id != apikey_id
            ).first()
            if existing_apikey:
                return error_response("API Key名称已存在，请使用不同的名称")
        
        for field, value in update_data.items():
            setattr(db_apikey, field, value)
    
    db_apikey.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_apikey)
    
    # 清除 API Key 缓存，确保状态变更后能及时更新
    clear_apikey_cache()
    
    # 同步到 workflow-ctl（失败不影响主流程）
    try:
        sync_success = await sync_apikey_to_workflow_ctl(
            external_id=db_apikey.id,
            name=db_apikey.name,
            description=db_apikey.description,
            key=db_apikey.key,
            status=db_apikey.status
        )
        if not sync_success:
            logger.warning(f"API Key 更新成功，但同步到 workflow-ctl 失败: id={db_apikey.id}")
        else:
            logger.info(f"API Key 更新并同步到 workflow-ctl 成功: id={db_apikey.id}")
    except Exception as e:
        # 同步失败不影响主流程，只记录日志
        logger.error(f"API Key 更新成功，但同步到 workflow-ctl 时发生异常: id={db_apikey.id}, error={str(e)}")
    
    return success_response("API Key更新成功", ApiKey.from_orm(db_apikey))

@router.delete("/delete", response_model=ApiResponse)
async def delete_apikey(apikey_id: str = Query(..., description="API Key ID"), db: Session = Depends(get_db)):
    """删除API Key"""
    db_apikey = db.query(ApiKeyModel).filter(ApiKeyModel.id == apikey_id).first()
    if not db_apikey:
        return not_found_error("API Key")
    
    # 先同步删除到 workflow-ctl（失败不影响主流程）
    try:
        delete_success = await delete_from_workflow_ctl("apikeys", db_apikey.id)
        if not delete_success:
            logger.warning(f"API Key 删除同步到 workflow-ctl 失败: id={db_apikey.id}")
    except Exception as e:
        # 同步失败不影响主流程，只记录日志
        logger.error(f"API Key 删除同步到 workflow-ctl 时发生异常: id={db_apikey.id}, error={str(e)}")
    
    db.delete(db_apikey)
    db.commit()
    
    # 清除 API Key 缓存，确保删除后能及时更新
    clear_apikey_cache()
    
    return success_response("API Key删除成功")

@router.get("/stats", response_model=ApiResponse)
async def get_apikey_stats(db: Session = Depends(get_db)):
    """获取API Key统计信息"""
    total_count = db.query(ApiKeyModel).count()
    return success_response("获取统计信息成功", {"total_count": total_count})

    # 清除 API Key 缓存，确保删除后能及时更新
    clear_apikey_cache()
    
    return success_response("API Key删除成功")

@router.get("/stats", response_model=ApiResponse)
async def get_apikey_stats(db: Session = Depends(get_db)):
    """获取API Key统计信息"""
    total_count = db.query(ApiKeyModel).count()
    return success_response("获取统计信息成功", {"total_count": total_count})

    # 清除 API Key 缓存，确保删除后能及时更新
    clear_apikey_cache()
    
    return success_response("API Key删除成功")

@router.get("/stats", response_model=ApiResponse)
async def get_apikey_stats(db: Session = Depends(get_db)):
    """获取API Key统计信息"""
    total_count = db.query(ApiKeyModel).count()
    return success_response("获取统计信息成功", {"total_count": total_count})