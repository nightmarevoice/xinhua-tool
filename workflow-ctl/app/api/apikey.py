from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.database.database import get_db
from app.models.apikey import ApiKey
from app.schemas.apikey import ApiKeySync, ApiKey as ApiKeySchema
from app.schemas.common import Response
from app.middleware.auth import verify_api_key_dependency

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 同步接口（供 backend 项目调用）====================

@router.post("/sync", response_model=Response)
def sync_apikey(
    apikey: ApiKeySync, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    同步 API Key（新增或更新）
    由 backend 项目调用，当 backend 中的 API Key 新增或修改时调用此接口
    
    支持基于 external_id 或 key 的 upsert 操作：
    1. 优先根据 external_id 查找记录
    2. 如果不存在，根据 key 查找记录
    3. 如果都不存在，创建新记录
    """
    logger.info(f"开始同步 API Key: external_id={apikey.external_id}, name={apikey.name}, key={apikey.key[:20]}...")
    
    # 优先检查是否已存在相同 external_id 的记录
    existing = db.query(ApiKey).filter(ApiKey.external_id == apikey.external_id).first()
    
    if existing:
        # 更新现有记录（基于 external_id）
        logger.info(f"发现现有记录（基于 external_id），准备更新: id={existing.id}, external_id={apikey.external_id}")
        
        # 如果 key 改变，检查新 key 是否已存在于其他记录中
        if existing.key != apikey.key:
            key_exists = db.query(ApiKey).filter(
                ApiKey.key == apikey.key,
                ApiKey.id != existing.id
            ).first()
            if key_exists:
                logger.warning(f"新 key 已存在于其他记录中: id={key_exists.id}, external_id={key_exists.external_id}")
                # 如果新 key 已存在，删除旧记录，更新已存在的记录
                db.delete(existing)
                db.flush()  # 确保删除操作完成
                existing = key_exists
        
        # 记录更新前的数据
        old_data = {
            "name": existing.name,
            "description": existing.description,
            "key": existing.key[:20] + "..." if len(existing.key) > 20 else existing.key,
            "status": existing.status
        }
        
        # 更新记录
        existing.external_id = apikey.external_id
        existing.name = apikey.name
        existing.description = apikey.description
        existing.key = apikey.key
        existing.status = apikey.status
        db.commit()
        db.refresh(existing)
        
        logger.info(f"API Key 更新成功: id={existing.id}, external_id={apikey.external_id}")
        logger.info(f"更新前: {old_data}")
        logger.info(f"更新后: name={existing.name}, description={existing.description}, status={existing.status}")
        
        return Response(
            success=True,
            message="更新成功",
            data=ApiKeySchema.model_validate(existing)
        )
    else:
        # 检查是否已存在相同 key 的记录
        existing_by_key = db.query(ApiKey).filter(ApiKey.key == apikey.key).first()
        
        if existing_by_key:
            # 更新现有记录（基于 key）
            logger.info(f"发现现有记录（基于 key），准备更新: id={existing_by_key.id}, key={apikey.key[:20]}...")
            
            # 记录更新前的数据
            old_data = {
                "external_id": existing_by_key.external_id,
                "name": existing_by_key.name,
                "description": existing_by_key.description,
                "status": existing_by_key.status
            }
            
            existing_by_key.external_id = apikey.external_id
            existing_by_key.name = apikey.name
            existing_by_key.description = apikey.description
            existing_by_key.status = apikey.status
            db.commit()
            db.refresh(existing_by_key)
            
            logger.info(f"API Key 更新成功（基于 key）: id={existing_by_key.id}, external_id={apikey.external_id}")
            logger.info(f"更新前: {old_data}")
            logger.info(f"更新后: name={existing_by_key.name}, description={existing_by_key.description}, status={existing_by_key.status}")
            
            return Response(
                success=True,
                message="更新成功",
                data=ApiKeySchema.model_validate(existing_by_key)
            )
        else:
            # 创建新记录
            logger.info(f"创建新的 API Key 记录: external_id={apikey.external_id}")
            
            db_apikey = ApiKey(
                external_id=apikey.external_id,
                name=apikey.name,
                description=apikey.description,
                key=apikey.key,
                status=apikey.status
            )
            db.add(db_apikey)
            db.commit()
            db.refresh(db_apikey)
            
            logger.info(f"API Key 创建成功: id={db_apikey.id}, external_id={apikey.external_id}")
            
            return Response(
                success=True,
                message="创建成功",
                data=ApiKeySchema.model_validate(db_apikey)
            )


@router.delete("/sync/{external_id}", response_model=Response)
def delete_apikey_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 删除 API Key
    由 backend 项目调用，当 backend 中的 API Key 删除时调用此接口
    """
    logger.info(f"开始删除 API Key: external_id={external_id}")
    
    db_apikey = db.query(ApiKey).filter(ApiKey.external_id == external_id).first()
    if not db_apikey:
        logger.warning(f"API Key 未找到: external_id={external_id}")
        raise HTTPException(status_code=404, detail="API Key not found")
    
    logger.info(f"找到要删除的 API Key: id={db_apikey.id}, name={db_apikey.name}")
    
    db.delete(db_apikey)
    db.commit()
    
    logger.info(f"API Key 删除成功: external_id={external_id}")
    
    return Response(
        success=True,
        message="删除成功"
    )


# ==================== 数据读取接口 ====================

@router.get("/list", response_model=Response)
def get_synced_apikeys(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    search: Optional[str] = Query(None, description="按名称或描述搜索"),
    db: Session = Depends(get_db)
):
    """
    获取同步的 API Key 数据集合
    支持分页、状态筛选和搜索功能
    """
    logger.info(f"查询 API Key 数据: skip={skip}, limit={limit}, status={status}, search={search}")
    
    try:
        # 构建查询
        query = db.query(ApiKey)
        
        # 状态筛选
        if status:
            query = query.filter(ApiKey.status == status)
            logger.info(f"应用状态筛选: {status}")
        
        # 搜索功能
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (ApiKey.name.ilike(search_filter)) | 
                (ApiKey.description.ilike(search_filter))
            )
            logger.info(f"应用搜索筛选: {search}")
        
        # 获取总数
        total = query.count()
        logger.info(f"查询到 {total} 条记录")
        
        # 分页查询
        apikeys = query.offset(skip).limit(limit).all()
        
        # 转换为响应格式
        apikey_data = [ApiKeySchema.model_validate(apikey) for apikey in apikeys]
        
        logger.info(f"返回 {len(apikey_data)} 条记录")
        
        return Response(
            success=True,
            message=f"查询成功，共 {total} 条记录",
            data={
                "items": apikey_data,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(apikey_data) < total
            }
        )
        
    except Exception as e:
        logger.error(f"查询 API Key 数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/get/{external_id}", response_model=Response)
def get_apikey_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 获取单个 API Key
    """
    logger.info(f"查询单个 API Key: external_id={external_id}")
    
    try:
        apikey = db.query(ApiKey).filter(ApiKey.external_id == external_id).first()
        
        if not apikey:
            logger.warning(f"API Key 未找到: external_id={external_id}")
            raise HTTPException(status_code=404, detail="API Key not found")
        
        logger.info(f"找到 API Key: id={apikey.id}, name={apikey.name}")
        
        return Response(
            success=True,
            message="查询成功",
            data=ApiKeySchema.model_validate(apikey)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询 API Key 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats", response_model=Response)
def get_apikey_stats(
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    获取 API Key 统计信息
    """
    logger.info("查询 API Key 统计信息")
    
    try:
        # 总数量
        total_count = db.query(ApiKey).count()
        
        # 按状态统计
        status_stats = {}
        for status in ['active', 'inactive', 'expired']:
            count = db.query(ApiKey).filter(ApiKey.status == status).count()
            status_stats[status] = count
        
        # 最近创建的记录数（最近7天）
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = db.query(ApiKey).filter(ApiKey.created_at >= week_ago).count()
        
        stats = {
            "total_count": total_count,
            "status_distribution": status_stats,
            "recent_created": recent_count,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        logger.info(f"统计信息: {stats}")
        
        return Response(
            success=True,
            message="统计信息获取成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
