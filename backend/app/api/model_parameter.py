from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import uuid
from datetime import datetime
import logging

from app.database import get_db
from app.models.model_parameter import ModelParameter as ModelParameterModel
from app.models.llm_provider import LLMProvider
from app.schemas.model_parameter import ModelParameter, ModelParameterCreate, ModelParameterUpdate
from app.schemas.common import PaginatedResponse, ApiResponse
from app.utils.response import error_response, success_response, not_found_error
from app.utils.workflow_ctl_sync import sync_model_parameter_to_workflow_ctl, delete_from_workflow_ctl

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/list", response_model=PaginatedResponse)
async def get_model_parameters(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    model_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取模型参数列表"""
    query = db.query(ModelParameterModel)
    
    if search:
        query = query.filter(
            ModelParameterModel.name.contains(search) | 
            ModelParameterModel.description.contains(search)
        )
    
    if model_type:
        query = query.filter(ModelParameterModel.model_type == model_type)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    from app.schemas.common import PaginatedData
    
    return PaginatedResponse[ModelParameter](
        data=PaginatedData[ModelParameter](
            items=[ModelParameter.from_orm(item) for item in items],
            total=total,
            page=page,
            page_size=page_size
        )
    )

@router.get("/get", response_model=ApiResponse)
async def get_model_parameter(parameter_id: str = Query(..., description="Parameter ID"), db: Session = Depends(get_db)):
    """获取单个模型参数"""
    parameter = db.query(ModelParameterModel).filter(ModelParameterModel.id == parameter_id).first()
    if not parameter:
        return not_found_error("Model parameter")
    
    return success_response("获取模型参数成功", ModelParameter.from_orm(parameter))

@router.post("/create", response_model=ApiResponse)
async def create_model_parameter(parameter: ModelParameterCreate, db: Session = Depends(get_db)):
    """创建模型参数"""
    db_parameter = ModelParameterModel(
        id=str(uuid.uuid4()),
        name=parameter.name,
        type=parameter.type,
        default_value=parameter.default_value,
        model_type=parameter.model_type,
        description=parameter.description,
        required=parameter.required,
        validation=parameter.validation
    )
    
    db.add(db_parameter)
    db.commit()
    db.refresh(db_parameter)
    
    # 同步到 workflow-ctl
    sync_success = await sync_model_parameter_to_workflow_ctl(
        external_id=db_parameter.id,
        name=db_parameter.name,
        type=db_parameter.type,
        default_value=db_parameter.default_value,
        model_type=db_parameter.model_type,
        description=db_parameter.description,
        required=db_parameter.required,
        validation=db_parameter.validation
    )
    
    if not sync_success:
        logger.warning(f"模型参数创建成功，但同步到 workflow-ctl 失败: parameter_id={db_parameter.id}")
        # 注意：即使同步失败，也返回成功，因为本地数据已保存
        # 可以考虑添加重试机制或异步队列
    
    return success_response("模型参数创建成功", ModelParameter.from_orm(db_parameter))

@router.put("/update", response_model=ApiResponse)
async def update_model_parameter(
    parameter_id: str = Query(..., description="Parameter ID"),
    parameter: ModelParameterUpdate = Body(None, description="更新数据"),
    db: Session = Depends(get_db)
):
    """更新模型参数"""
    db_parameter = db.query(ModelParameterModel).filter(ModelParameterModel.id == parameter_id).first()
    if not db_parameter:
        return not_found_error("Model parameter")
    
    # 更新字段
    if parameter is None:
        return error_response("请提供要更新的字段")
    
    update_data = parameter.model_dump(exclude_unset=True)
    if not update_data:
        return error_response("没有提供要更新的字段")
    
    for field, value in update_data.items():
        setattr(db_parameter, field, value)
    
    db_parameter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_parameter)
    
    # 同步到 workflow-ctl
    sync_success = await sync_model_parameter_to_workflow_ctl(
        external_id=db_parameter.id,
        name=db_parameter.name,
        type=db_parameter.type,
        default_value=db_parameter.default_value,
        model_type=db_parameter.model_type,
        description=db_parameter.description,
        required=db_parameter.required,
        validation=db_parameter.validation
    )
    
    if not sync_success:
        logger.warning(f"模型参数更新成功，但同步到 workflow-ctl 失败: parameter_id={parameter_id}")
        # 注意：即使同步失败，也返回成功，因为本地数据已保存
        # 可以考虑添加重试机制或异步队列
    
    return success_response("模型参数更新成功", ModelParameter.from_orm(db_parameter))

@router.delete("/delete", response_model=ApiResponse)
async def delete_model_parameter(parameter_id: str = Query(..., description="Parameter ID"), db: Session = Depends(get_db)):
    """删除模型参数"""
    db_parameter = db.query(ModelParameterModel).filter(ModelParameterModel.id == parameter_id).first()
    if not db_parameter:
        return not_found_error("Model parameter")
    
    # 先同步删除到 workflow-ctl（失败不影响主流程）
    try:
        delete_success = await delete_from_workflow_ctl("model-parameters", db_parameter.id)
        if not delete_success:
            logger.warning(f"模型参数删除同步到 workflow-ctl 失败: id={db_parameter.id}")
    except Exception as e:
        # 同步失败不影响主流程，只记录日志
        logger.error(f"模型参数删除同步到 workflow-ctl 时发生异常: id={db_parameter.id}, error={str(e)}")
    
    db.delete(db_parameter)
    db.commit()
    
    return success_response("模型参数删除成功")

@router.get("/stats", response_model=ApiResponse)
async def get_model_parameter_stats(db: Session = Depends(get_db)):
    """获取LLM Provider统计信息"""
    total_count = db.query(LLMProvider).count()
    return success_response("获取统计信息成功", {"total_count": total_count})