from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from app.database import get_db
from app.models.workflow import Workflow as WorkflowModel
from app.schemas.workflow import Workflow, WorkflowCreate, WorkflowUpdate
from app.schemas.common import PaginatedResponse, ApiResponse
from app.utils.response import error_response, success_response, not_found_error
from app.utils.workflow_ctl_sync import sync_workflow_to_workflow_ctl

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/list", response_model=PaginatedResponse)
async def get_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取流程列表"""
    query = db.query(WorkflowModel)
    
    if search:
        query = query.filter(
            WorkflowModel.name.contains(search) | 
            WorkflowModel.description.contains(search)
        )
    
    if type:
        query = query.filter(WorkflowModel.type == type)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    from app.schemas.common import PaginatedData
    
    return PaginatedResponse[Workflow](
        data=PaginatedData[Workflow](
            items=[Workflow.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size
        )
    )

@router.get("/get", response_model=ApiResponse)
async def get_workflow(workflow_id: str = Query(..., description="Workflow ID"), db: Session = Depends(get_db)):
    """获取单个流程"""
    workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not workflow:
        return not_found_error("Workflow")
    
    return success_response("获取流程成功", Workflow.model_validate(workflow))

@router.post("/create", response_model=ApiResponse)
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """创建流程"""
    db_workflow = WorkflowModel(
        id=str(uuid.uuid4()),
        name=workflow.name,
        description=workflow.description,
        type=workflow.type,
        status="active"
    )
    
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    
    # 同步到 workflow-ctl
    sync_success = await sync_workflow_to_workflow_ctl(
        external_id=db_workflow.id,
        name=db_workflow.name,
        description=db_workflow.description,
        workflow_type=db_workflow.type,
        config=None,  # backend 的 workflow 没有 config，使用默认配置
        status=db_workflow.status
    )
    
    if not sync_success:
        logger.warning(f"流程创建成功，但同步到 workflow-ctl 失败: workflow_id={db_workflow.id}")
        # 注意：即使同步失败，也返回成功，因为本地数据已保存
        # 可以考虑添加重试机制或异步队列
    
    return success_response("流程创建成功", Workflow.model_validate(db_workflow))

@router.put("/update", response_model=ApiResponse)
async def update_workflow(
    workflow_id: str = Query(..., description="Workflow ID"),
    workflow: WorkflowUpdate = Body(..., description="更新数据"),
    db: Session = Depends(get_db)
):
    """更新流程"""
    db_workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not db_workflow:
        return not_found_error("Workflow")
    
    # 更新字段
    update_data = workflow.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_workflow, field, value)
    
    db_workflow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_workflow)
    
    # 同步到 workflow-ctl
    sync_success = await sync_workflow_to_workflow_ctl(
        external_id=db_workflow.id,
        name=db_workflow.name,
        description=db_workflow.description,
        workflow_type=db_workflow.type,
        config=None,  # backend 的 workflow 没有 config，使用默认配置
        status=db_workflow.status
    )
    
    if not sync_success:
        logger.warning(f"流程更新成功，但同步到 workflow-ctl 失败: workflow_id={workflow_id}")
        # 注意：即使同步失败，也返回成功，因为本地数据已保存
        # 可以考虑添加重试机制或异步队列
    
    return success_response("流程更新成功", Workflow.model_validate(db_workflow))

@router.delete("/delete", response_model=ApiResponse)
async def delete_workflow(workflow_id: str = Query(..., description="Workflow ID"), db: Session = Depends(get_db)):
    """删除流程"""
    db_workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not db_workflow:
        return not_found_error("Workflow")
    
    db.delete(db_workflow)
    db.commit()
    
    # 同步到 workflow-ctl
    from app.utils.workflow_ctl_sync import delete_from_workflow_ctl
    sync_success = await delete_from_workflow_ctl("workflows", workflow_id)
    
    if not sync_success:
        logger.warning(f"流程删除成功，但同步到 workflow-ctl 失败: workflow_id={workflow_id}")
        # 注意：即使同步失败，也返回成功，因为本地数据已删除
        # 可以考虑添加重试机制或异步队列
    
    return success_response("流程删除成功")

@router.get("/stats", response_model=ApiResponse)
async def get_workflow_stats(db: Session = Depends(get_db)):
    """获取流程统计信息"""
    total_count = db.query(WorkflowModel).count()
    return success_response("获取统计信息成功", {"total_count": total_count})
