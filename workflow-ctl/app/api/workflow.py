from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.database.database import get_db
from app.models.workflow import Workflow
from app.models.apikey import ApiKey
from app.schemas.workflow import WorkflowSync, Workflow as WorkflowSchema
from app.schemas.common import Response
from app.middleware.auth import verify_api_key_dependency

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 同步接口（供 backend 项目调用）====================

@router.post("/sync", response_model=Response)
def sync_workflow(
    workflow: WorkflowSync, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    同步流程配置（新增或更新）
    由 backend 项目调用，当 backend 中的流程配置新增或修改时调用此接口
    """
    try:
        logger.info(f"开始同步流程配置: external_id={workflow.external_id}, backend_id={workflow.backend_id}, name={workflow.name}")
        logger.debug(f"同步数据: external_id={workflow.external_id}, backend_id={workflow.backend_id}, name={workflow.name}, workflow_type={workflow.workflow_type}, config={workflow.config}")
        
        # 检查是否已存在相同 external_id 的记录
        existing = db.query(Workflow).filter(Workflow.external_id == workflow.external_id).first()
        
        if existing:
            # 更新现有记录
            logger.info(f"发现现有记录，准备更新: id={existing.id}, external_id={workflow.external_id}")
            
            # 记录更新前的数据
            old_data = {
                "name": existing.name,
                "description": existing.description,
                "workflow_type": existing.workflow_type,
                "backend_id": existing.backend_id
            }
            
            try:
                existing.name = workflow.name
                existing.description = workflow.description
                existing.workflow_type = workflow.workflow_type
                existing.config = workflow.config
                existing.backend_id = workflow.backend_id  # 更新原始字符串 ID
                existing.status = workflow.status  # 更新状态
                db.commit()
                db.refresh(existing)
                
                logger.info(f"流程配置更新成功: id={existing.id}, external_id={workflow.external_id}")
                logger.info(f"更新前: {old_data}")
                logger.info(f"更新后: name={existing.name}, workflow_type={existing.workflow_type}, backend_id={existing.backend_id}")
                
                return Response(
                    success=True,
                    message="更新成功",
                    data=WorkflowSchema.model_validate(existing)
                )
            except Exception as e:
                db.rollback()
                logger.error(f"更新流程配置时发生数据库错误: external_id={workflow.external_id}, 错误: {str(e)}")
                import traceback
                logger.error(f"详细错误堆栈: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
        else:
            # 创建新记录
            logger.info(f"创建新的流程配置记录: external_id={workflow.external_id}, backend_id={workflow.backend_id}")
            
            try:
                db_workflow = Workflow(
                    external_id=workflow.external_id,
                    backend_id=workflow.backend_id,  # 保存原始字符串 ID
                    name=workflow.name,
                    description=workflow.description,
                    workflow_type=workflow.workflow_type,
                    config=workflow.config,
                    status=workflow.status
                )
                db.add(db_workflow)
                db.commit()
                db.refresh(db_workflow)
                
                logger.info(f"流程配置创建成功: id={db_workflow.id}, external_id={workflow.external_id}, backend_id={db_workflow.backend_id}")
                
                return Response(
                    success=True,
                    message="创建成功",
                    data=WorkflowSchema.model_validate(db_workflow)
                )
            except Exception as e:
                db.rollback()
                logger.error(f"创建流程配置时发生数据库错误: external_id={workflow.external_id}, 错误: {str(e)}")
                import traceback
                logger.error(f"详细错误堆栈: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
                
    except ValueError as e:
        logger.error(f"流程配置同步失败 (验证错误): external_id={workflow.external_id}, 错误: {str(e)}")
        raise HTTPException(status_code=400, detail=f"验证失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流程配置同步失败 (未知错误): external_id={workflow.external_id}, 错误类型: {type(e).__name__}, 错误: {str(e)}")
        import traceback
        logger.error(f"详细错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.delete("/sync/{external_id}", response_model=Response)
def delete_workflow_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 删除流程配置
    由 backend 项目调用，当 backend 中的流程配置删除时调用此接口
    """
    logger.info(f"开始删除流程配置: external_id={external_id}")
    
    db_workflow = db.query(Workflow).filter(Workflow.external_id == external_id).first()
    if not db_workflow:
        logger.warning(f"流程配置未找到: external_id={external_id}")
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    logger.info(f"找到要删除的流程配置: id={db_workflow.id}, name={db_workflow.name}")
    
    db.delete(db_workflow)
    db.commit()
    
    logger.info(f"流程配置删除成功: external_id={external_id}")
    
    return Response(
        success=True,
        message="删除成功"
    )


# ==================== 数据读取接口 ====================

@router.get("/list", response_model=Response)
def get_synced_workflows(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    workflow_type: Optional[str] = Query(None, description="按流程类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选（active/inactive）"),
    search: Optional[str] = Query(None, description="按名称或描述搜索"),
    db: Session = Depends(get_db)
):
    """
    获取同步的流程配置数据集合
    支持分页、类型筛选、状态筛选和搜索功能
    """
    logger.info(f"查询流程配置数据: skip={skip}, limit={limit}, workflow_type={workflow_type}, status={status}, search={search}")
    
    try:
        # 构建查询
        query = db.query(Workflow)
        
        # 类型筛选
        if workflow_type:
            query = query.filter(Workflow.workflow_type == workflow_type)
            logger.info(f"应用类型筛选: {workflow_type}")
        
        # 状态筛选
        if status:
            query = query.filter(Workflow.status == status)
            logger.info(f"应用状态筛选: {status}")
        
        # 搜索功能
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Workflow.name.ilike(search_filter)) | 
                (Workflow.description.ilike(search_filter))
            )
            logger.info(f"应用搜索筛选: {search}")
        
        # 获取总数
        total = query.count()
        logger.info(f"查询到 {total} 条记录")
        
        # 分页查询
        workflows = query.offset(skip).limit(limit).all()
        
        # 转换为响应格式
        workflow_data = [WorkflowSchema.model_validate(workflow) for workflow in workflows]
        
        logger.info(f"返回 {len(workflow_data)} 条记录")
        
        return Response(
            success=True,
            message=f"查询成功，共 {total} 条记录",
            data={
                "items": workflow_data,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(workflow_data) < total
            }
        )
        
    except Exception as e:
        logger.error(f"查询流程配置数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/get/{external_id}", response_model=Response)
def get_workflow_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 获取单个流程配置
    """
    logger.info(f"查询单个流程配置: external_id={external_id}")
    
    try:
        workflow = db.query(Workflow).filter(Workflow.external_id == external_id).first()
        
        if not workflow:
            logger.warning(f"流程配置未找到: external_id={external_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(f"找到流程配置: id={workflow.id}, name={workflow.name}")
        
        return Response(
            success=True,
            message="查询成功",
            data=WorkflowSchema.model_validate(workflow)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询流程配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats", response_model=Response)
def get_workflow_stats(
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    获取流程配置统计信息
    """
    logger.info("查询流程配置统计信息")
    
    try:
        # 总数量
        total_count = db.query(Workflow).count()
        
        # 按类型统计
        type_stats = {}
        workflow_types = db.query(Workflow.workflow_type).distinct().all()
        for (workflow_type,) in workflow_types:
            count = db.query(Workflow).filter(Workflow.workflow_type == workflow_type).count()
            type_stats[workflow_type] = count
        
        # 最近创建的记录数（最近7天）
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = db.query(Workflow).filter(Workflow.created_at >= week_ago).count()
        
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
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
