from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.database.database import get_db
from app.models.llm_provider import LLMProvider
from app.models.apikey import ApiKey
from app.schemas.llm_provider import LLMProviderSync, LLMProvider as LLMProviderSchema
from app.schemas.common import Response
from app.middleware.auth import verify_api_key_dependency

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 同步接口（供 backend 项目调用）====================

@router.post("/sync", response_model=Response)
def sync_llm_provider(
    provider: LLMProviderSync, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    同步 LLM Provider（新增或更新）
    由 backend 项目调用，当 backend 中的 LLM Provider 新增或修改时调用此接口
    """
    logger.info(f"开始同步 LLM Provider: external_id={provider.external_id}, name={provider.name}")
    
    # 检查是否已存在相同 external_id 的记录
    existing = db.query(LLMProvider).filter(LLMProvider.external_id == provider.external_id).first()
    
    if existing:
        # 更新现有记录
        logger.info(f"发现现有记录，准备更新: id={existing.id}, external_id={provider.external_id}")
        
        # 记录更新前的数据
        old_data = {
            "name": existing.name,
            "provider": existing.provider,
            "default_model_name": existing.default_model_name
        }
        
        existing.name = provider.name
        existing.provider = provider.provider
        existing.api_key = provider.api_key
        existing.api_base = provider.api_base
        existing.api_version = provider.api_version
        existing.custom_config = provider.custom_config
        existing.default_model_name = provider.default_model_name
        existing.fast_default_model_name = provider.fast_default_model_name
        existing.deployment_name = provider.deployment_name
        existing.default_vision_model = provider.default_vision_model
        existing.model_configurations = provider.model_configurations
        existing.category = provider.category
        existing.is_default_provider = provider.is_default_provider
        existing.is_default_vision_provider = provider.is_default_vision_provider
        
        db.commit()
        db.refresh(existing)
        
        logger.info(f"LLM Provider 更新成功: id={existing.id}, external_id={provider.external_id}")
        logger.info(f"更新前: {old_data}")
        logger.info(f"更新后: name={existing.name}, provider={existing.provider}, default_model_name={existing.default_model_name}")
        
        return Response(
            success=True,
            message="更新成功",
            data=LLMProviderSchema.model_validate(existing)
        )
    else:
        # 创建新记录
        logger.info(f"创建新的 LLM Provider 记录: external_id={provider.external_id}")
        
        db_provider = LLMProvider(
            external_id=provider.external_id,
            name=provider.name,
            provider=provider.provider,
            api_key=provider.api_key,
            api_base=provider.api_base,
            api_version=provider.api_version,
            custom_config=provider.custom_config,
            default_model_name=provider.default_model_name,
            fast_default_model_name=provider.fast_default_model_name,
            deployment_name=provider.deployment_name,
            default_vision_model=provider.default_vision_model,
            model_configurations=provider.model_configurations,
            category=provider.category,
            is_default_provider=provider.is_default_provider,
            is_default_vision_provider=provider.is_default_vision_provider
        )
        db.add(db_provider)
        db.commit()
        db.refresh(db_provider)
        
        logger.info(f"LLM Provider 创建成功: id={db_provider.id}, external_id={provider.external_id}")
        
        return Response(
            success=True,
            message="创建成功",
            data=LLMProviderSchema.model_validate(db_provider)
        )


@router.delete("/sync/{external_id}", response_model=Response)
def delete_llm_provider_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 删除 LLM Provider
    由 backend 项目调用，当 backend 中的 LLM Provider 删除时调用此接口
    """
    logger.info(f"开始删除 LLM Provider: external_id={external_id}")
    
    db_provider = db.query(LLMProvider).filter(LLMProvider.external_id == external_id).first()
    if not db_provider:
        logger.warning(f"LLM Provider 未找到: external_id={external_id}")
        raise HTTPException(status_code=404, detail="LLM Provider not found")
    
    logger.info(f"找到要删除的 LLM Provider: id={db_provider.id}, name={db_provider.name}")
    
    db.delete(db_provider)
    db.commit()
    
    logger.info(f"LLM Provider 删除成功: external_id={external_id}")
    
    return Response(
        success=True,
        message="删除成功",
        data=None
    )


# ==================== 数据读取接口 ====================

@router.get("/list", response_model=Response)
def get_synced_llm_providers(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    provider: Optional[str] = Query(None, description="按 provider 类型筛选（openai, azure, anthropic 等）"),
    category: Optional[str] = Query(None, description="按 category 筛选（general, professional）"),
    is_default_provider: Optional[bool] = Query(None, description="按是否为默认 provider 筛选"),
    search: Optional[str] = Query(None, description="按名称或模型名称搜索"),
    db: Session = Depends(get_db)
):
    """
    获取同步的 LLM Provider 数据集合
    支持分页、类型筛选和搜索功能
    """
    logger.info(f"查询 LLM Provider 数据: skip={skip}, limit={limit}, provider={provider}, category={category}, search={search}")
    
    try:
        # 构建查询
        query = db.query(LLMProvider)
        
        # provider 类型筛选
        if provider:
            query = query.filter(LLMProvider.provider == provider)
            logger.info(f"应用 provider 筛选: {provider}")
        
        # category 筛选
        if category:
            query = query.filter(LLMProvider.category == category)
            logger.info(f"应用 category 筛选: {category}")
        
        # is_default_provider 筛选
        if is_default_provider is not None:
            query = query.filter(LLMProvider.is_default_provider == is_default_provider)
            logger.info(f"应用 is_default_provider 筛选: {is_default_provider}")
        
        # 搜索功能
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (LLMProvider.name.ilike(search_filter)) | 
                (LLMProvider.default_model_name.ilike(search_filter)) |
                (LLMProvider.fast_default_model_name.ilike(search_filter))
            )
            logger.info(f"应用搜索筛选: {search}")
        
        # 获取总数
        total = query.count()
        logger.info(f"查询到 {total} 条记录")
        
        # 分页查询
        providers = query.offset(skip).limit(limit).all()
        
        # 转换为响应格式
        provider_data = [LLMProviderSchema.model_validate(provider) for provider in providers]
        
        logger.info(f"返回 {len(provider_data)} 条记录")
        
        return Response(
            success=True,
            message=f"查询成功，共 {total} 条记录",
            data={
                "items": provider_data,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(provider_data) < total
            }
        )
        
    except Exception as e:
        logger.error(f"查询 LLM Provider 数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/get/{external_id}", response_model=Response)
def get_llm_provider_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 获取单个 LLM Provider
    """
    logger.info(f"查询单个 LLM Provider: external_id={external_id}")
    
    try:
        provider = db.query(LLMProvider).filter(LLMProvider.external_id == external_id).first()
        
        if not provider:
            logger.warning(f"LLM Provider 未找到: external_id={external_id}")
            raise HTTPException(status_code=404, detail="LLM Provider not found")
        
        logger.info(f"找到 LLM Provider: id={provider.id}, name={provider.name}")
        
        return Response(
            success=True,
            message="查询成功",
            data=LLMProviderSchema.model_validate(provider)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询 LLM Provider 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats", response_model=Response)
def get_llm_provider_stats(
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    获取 LLM Provider 统计信息
    """
    logger.info("查询 LLM Provider 统计信息")
    
    try:
        # 总数量
        total_count = db.query(LLMProvider).count()
        
        # 按 provider 类型统计
        from sqlalchemy import func
        provider_stats = {}
        provider_counts = db.query(
            LLMProvider.provider,
            func.count(LLMProvider.id).label('count')
        ).group_by(LLMProvider.provider).all()
        
        for provider_type, count in provider_counts:
            provider_stats[provider_type] = count
        
        # 按 category 统计
        category_stats = {}
        category_counts = db.query(
            LLMProvider.category,
            func.count(LLMProvider.id).label('count')
        ).group_by(LLMProvider.category).all()
        
        for cat, count in category_counts:
            category_stats[cat] = count
        
        # 默认 provider 统计
        default_provider_count = db.query(LLMProvider).filter(LLMProvider.is_default_provider == True).count()
        default_vision_provider_count = db.query(LLMProvider).filter(LLMProvider.is_default_vision_provider == True).count()
        
        # 最近创建的记录数（最近7天）
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = db.query(LLMProvider).filter(LLMProvider.created_at >= week_ago).count()
        
        stats = {
            "total_count": total_count,
            "provider_distribution": provider_stats,
            "category_distribution": category_stats,
            "default_provider_count": default_provider_count,
            "default_vision_provider_count": default_vision_provider_count,
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

