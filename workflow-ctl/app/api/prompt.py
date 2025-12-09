from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.database.database import get_db
from app.models.prompt import Prompt
from app.models.apikey import ApiKey
from app.schemas.prompt import PromptSync, Prompt as PromptSchema
from app.schemas.common import Response
from app.middleware.auth import verify_api_key_dependency

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 同步接口（供 backend 项目调用）====================

@router.post("/sync", response_model=Response)
def sync_prompt(
    prompt: PromptSync, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    同步 Prompt 配置（新增或更新）
    由 backend 项目调用，当 backend 中的 Prompt 配置新增或修改时调用此接口
    """
    try:
        logger.info(f"开始同步 Prompt 配置: external_id={prompt.external_id}, title={prompt.title}, model_type={prompt.model_type}")
        
        # 验证必需字段
        if not prompt.title:
            raise ValueError("title 不能为空")
        if not prompt.model_type:
            raise ValueError("model_type 不能为空")
        
        # 检查是否已存在相同 external_id 的记录
        existing = db.query(Prompt).filter(Prompt.external_id == prompt.external_id).first()
        
        if existing:
            # 更新现有记录
            logger.info(f"发现现有记录，准备更新: id={existing.id}, external_id={prompt.external_id}")
            
            # 记录更新前的数据
            old_data = {
                "title": existing.title,
                "model_type": existing.model_type,
                "system_prompt": existing.system_prompt[:50] if existing.system_prompt else None,
                "user_prompt": existing.user_prompt[:50] if existing.user_prompt else None
            }
            
            try:
                existing.title = prompt.title
                existing.system_prompt = prompt.system_prompt
                existing.user_prompt = prompt.user_prompt
                existing.model_type = prompt.model_type
                db.commit()
                db.refresh(existing)
                
                logger.info(f"Prompt 配置更新成功: id={existing.id}, external_id={prompt.external_id}")
                logger.info(f"更新前: {old_data}")
                logger.info(f"更新后: title={existing.title}, model_type={existing.model_type}")
                
                return Response(
                    success=True,
                    message="更新成功",
                    data=PromptSchema.model_validate(existing)
                )
            except Exception as e:
                db.rollback()
                logger.error(f"更新 Prompt 配置时发生数据库错误: external_id={prompt.external_id}, 错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
        else:
            # 创建新记录
            logger.info(f"创建新的 Prompt 配置记录: external_id={prompt.external_id}")
            
            try:
                db_prompt = Prompt(
                    external_id=prompt.external_id,
                    title=prompt.title,
                    system_prompt=prompt.system_prompt,
                    user_prompt=prompt.user_prompt,
                    model_type=prompt.model_type
                )
                db.add(db_prompt)
                db.commit()
                db.refresh(db_prompt)
                
                logger.info(f"Prompt 配置创建成功: id={db_prompt.id}, external_id={prompt.external_id}")
                
                return Response(
                    success=True,
                    message="创建成功",
                    data=PromptSchema.model_validate(db_prompt)
                )
            except Exception as e:
                db.rollback()
                logger.error(f"创建 Prompt 配置时发生数据库错误: external_id={prompt.external_id}, 错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
                
    except ValueError as e:
        logger.error(f"Prompt 配置同步失败 (验证错误): external_id={prompt.external_id}, 错误: {str(e)}")
        raise HTTPException(status_code=400, detail=f"验证失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prompt 配置同步失败 (未知错误): external_id={prompt.external_id}, 错误类型: {type(e).__name__}, 错误: {str(e)}")
        import traceback
        logger.error(f"详细错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.delete("/sync/{external_id}", response_model=Response)
def delete_prompt_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 删除 Prompt 配置
    由 backend 项目调用，当 backend 中的 Prompt 配置删除时调用此接口
    """
    logger.info(f"开始删除 Prompt 配置: external_id={external_id}")
    
    db_prompt = db.query(Prompt).filter(Prompt.external_id == external_id).first()
    if not db_prompt:
        logger.warning(f"Prompt 配置未找到: external_id={external_id}")
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    logger.info(f"找到要删除的 Prompt 配置: id={db_prompt.id}, title={db_prompt.title}")
    
    db.delete(db_prompt)
    db.commit()
    
    logger.info(f"Prompt 配置删除成功: external_id={external_id}")
    
    return Response(
        success=True,
        message="删除成功"
    )


# ==================== 数据读取接口 ====================

@router.get("/list", response_model=Response)
def get_synced_prompts(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    model_type: Optional[str] = Query(None, description="按模型类型筛选"),
    search: Optional[str] = Query(None, description="按标题或内容搜索"),
    db: Session = Depends(get_db)
):
    """
    获取同步的 Prompt 配置数据集合
    支持分页、类型筛选和搜索功能
    """
    logger.info(f"查询 Prompt 配置数据: skip={skip}, limit={limit}, model_type={model_type}, search={search}")
    
    try:
        # 构建查询
        query = db.query(Prompt)
        
        # 类型筛选
        if model_type:
            query = query.filter(Prompt.model_type == model_type)
            logger.info(f"应用类型筛选: {model_type}")
        
        # 搜索功能
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Prompt.title.ilike(search_filter)) | 
                (Prompt.system_prompt.ilike(search_filter)) |
                (Prompt.user_prompt.ilike(search_filter))
            )
            logger.info(f"应用搜索筛选: {search}")
        
        # 获取总数
        total = query.count()
        logger.info(f"查询到 {total} 条记录")
        
        # 分页查询
        prompts = query.offset(skip).limit(limit).all()
        
        # 转换为响应格式
        prompt_data = [PromptSchema.model_validate(prompt) for prompt in prompts]
        
        logger.info(f"返回 {len(prompt_data)} 条记录")
        
        return Response(
            success=True,
            message=f"查询成功，共 {total} 条记录",
            data={
                "items": prompt_data,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(prompt_data) < total
            }
        )
        
    except Exception as e:
        logger.error(f"查询 Prompt 配置数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/get/{external_id}", response_model=Response)
def get_prompt_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 获取单个 Prompt 配置
    """
    logger.info(f"查询单个 Prompt 配置: external_id={external_id}")
    
    try:
        prompt = db.query(Prompt).filter(Prompt.external_id == external_id).first()
        
        if not prompt:
            logger.warning(f"Prompt 配置未找到: external_id={external_id}")
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        logger.info(f"找到 Prompt 配置: id={prompt.id}, title={prompt.title}")
        
        return Response(
            success=True,
            message="查询成功",
            data=PromptSchema.model_validate(prompt)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询 Prompt 配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats", response_model=Response)
def get_prompt_stats(
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    获取 Prompt 配置统计信息
    """
    logger.info("查询 Prompt 配置统计信息")
    
    try:
        # 总数量
        total_count = db.query(Prompt).count()
        
        # 按模型类型统计
        type_stats = {}
        model_types = db.query(Prompt.model_type).distinct().all()
        for (model_type,) in model_types:
            count = db.query(Prompt).filter(Prompt.model_type == model_type).count()
            type_stats[model_type] = count
        
        # 最近创建的记录数（最近7天）
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = db.query(Prompt).filter(Prompt.created_at >= week_ago).count()
        
        stats = {
            "total_count": total_count,
            "type_distribution": type_stats,
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