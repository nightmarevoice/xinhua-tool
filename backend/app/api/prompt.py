from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from app.database import get_db
from app.models.prompt import Prompt as PromptModel
from app.schemas.prompt import Prompt, PromptCreate, PromptUpdate
from app.schemas.common import PaginatedResponse, ApiResponse
from app.utils.response import error_response, success_response, not_found_error
from app.utils.workflow_ctl_sync import sync_prompt_to_workflow_ctl, delete_from_workflow_ctl

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/list", response_model=PaginatedResponse)
async def get_prompts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    model_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取Prompt列表"""
    query = db.query(PromptModel)
    
    if search:
        query = query.filter(
            PromptModel.title.contains(search) | 
            PromptModel.system_prompt.contains(search) |
            PromptModel.user_prompt.contains(search)
        )
    
    if model_type:
        query = query.filter(PromptModel.model_type == model_type)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    from app.schemas.common import PaginatedData
    
    return PaginatedResponse[Prompt](
        data=PaginatedData[Prompt](
            items=[Prompt.from_orm(item) for item in items],
            total=total,
            page=page,
            page_size=page_size
        )
    )

@router.get("/get", response_model=ApiResponse)
async def get_prompt(prompt_id: str = Query(..., description="Prompt ID"), db: Session = Depends(get_db)):
    """获取单个Prompt"""
    prompt = db.query(PromptModel).filter(PromptModel.id == prompt_id).first()
    if not prompt:
        return not_found_error("Prompt")
    
    return success_response("获取Prompt成功", Prompt.from_orm(prompt))

@router.post("/create", response_model=ApiResponse)
async def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    """创建Prompt"""
    db_prompt = PromptModel(
        id=str(uuid.uuid4()),
        title=prompt.title,
        system_prompt=prompt.system_prompt,
        user_prompt=prompt.user_prompt,
        model_type=prompt.model_type
    )
    
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    
    # 同步到 workflow-ctl
    logger.info(f"开始同步新创建的 Prompt 到 workflow-ctl: prompt_id={db_prompt.id}, title={db_prompt.title}, model_type={db_prompt.model_type}")
    sync_success = await sync_prompt_to_workflow_ctl(
        external_id=db_prompt.id,
        title=db_prompt.title,
        system_prompt=db_prompt.system_prompt,
        user_prompt=db_prompt.user_prompt,
        model_type=db_prompt.model_type
    )
    
    if not sync_success:
        logger.error(f"Prompt 创建成功但同步到 workflow-ctl 失败: prompt_id={db_prompt.id}, title={db_prompt.title}")
        # 注意：即使同步失败，也返回成功，因为数据库已创建
        # 可以考虑记录到失败队列或重试机制
        return success_response(
            "Prompt创建成功，但同步到 workflow-ctl 失败，请检查日志", 
            Prompt.from_orm(db_prompt)
        )
    
    logger.info(f"Prompt 创建并同步成功: prompt_id={db_prompt.id}")
    return success_response("Prompt创建成功", Prompt.from_orm(db_prompt))

@router.put("/update", response_model=ApiResponse)
async def update_prompt(
    prompt_id: str = Query(..., description="Prompt ID"),
    prompt: PromptUpdate = Body(..., description="更新数据"),
    db: Session = Depends(get_db)
):
    """更新Prompt"""
    db_prompt = db.query(PromptModel).filter(PromptModel.id == prompt_id).first()
    if not db_prompt:
        return not_found_error("Prompt")
    
    # 更新字段
    update_data = prompt.model_dump(exclude_unset=True)
    if not update_data:
        return error_response("没有提供要更新的字段")
    
    logger.info(f"开始更新 Prompt: prompt_id={prompt_id}, 更新字段: {list(update_data.keys())}")
    
    for field, value in update_data.items():
        setattr(db_prompt, field, value)
    
    db_prompt.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_prompt)
    
    # 验证必需字段是否存在
    if not db_prompt.model_type:
        logger.error(f"Prompt 更新失败: model_type 不能为空, prompt_id={prompt_id}")
        return error_response("Prompt 的 model_type 不能为空")
    
    # 同步到 workflow-ctl
    logger.info(f"开始同步 Prompt 到 workflow-ctl: prompt_id={prompt_id}, title={db_prompt.title}, model_type={db_prompt.model_type}")
    sync_success = await sync_prompt_to_workflow_ctl(
        external_id=db_prompt.id,
        title=db_prompt.title,
        system_prompt=db_prompt.system_prompt,
        user_prompt=db_prompt.user_prompt,
        model_type=db_prompt.model_type
    )
    
    if not sync_success:
        logger.error(f"Prompt 更新成功但同步到 workflow-ctl 失败: prompt_id={prompt_id}, title={db_prompt.title}")
        # 注意：即使同步失败，也返回成功，因为数据库已更新
        # 可以考虑记录到失败队列或重试机制
        return success_response(
            "Prompt更新成功，但同步到 workflow-ctl 失败，请检查日志", 
            Prompt.from_orm(db_prompt)
        )
    
    logger.info(f"Prompt 更新并同步成功: prompt_id={prompt_id}")
    return success_response("Prompt更新成功", Prompt.from_orm(db_prompt))

@router.delete("/delete", response_model=ApiResponse)
async def delete_prompt(prompt_id: str = Query(..., description="Prompt ID"), db: Session = Depends(get_db)):
    """删除Prompt"""
    db_prompt = db.query(PromptModel).filter(PromptModel.id == prompt_id).first()
    if not db_prompt:
        return not_found_error("Prompt")
    
    # 同步删除到 workflow-ctl（在删除数据库记录之前调用）
    logger.info(f"开始同步删除 Prompt 到 workflow-ctl: prompt_id={prompt_id}, title={db_prompt.title}")
    delete_success = await delete_from_workflow_ctl("prompts", db_prompt.id)
    
    if not delete_success:
        logger.error(f"Prompt 删除同步到 workflow-ctl 失败: prompt_id={prompt_id}, title={db_prompt.title}")
        # 注意：即使同步失败，也继续删除数据库记录
        # 可以考虑记录到失败队列或重试机制
    
    db.delete(db_prompt)
    db.commit()
    
    if not delete_success:
        return success_response(
            "Prompt删除成功，但同步删除到 workflow-ctl 失败，请检查日志"
        )
    
    logger.info(f"Prompt 删除并同步成功: prompt_id={prompt_id}")
    return success_response("Prompt删除成功")

@router.get("/stats", response_model=ApiResponse)
async def get_prompt_stats(db: Session = Depends(get_db)):
    """获取Prompt统计信息"""
    total_count = db.query(PromptModel).count()
    return success_response("获取统计信息成功", {"total_count": total_count})
