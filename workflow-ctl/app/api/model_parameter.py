from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.database.database import get_db
from app.models.model_parameter import ModelParameter
from app.models.apikey import ApiKey
from app.schemas.model_parameter import ModelParameterSync, ModelParameter as ModelParameterSchema
from app.schemas.common import Response
from app.middleware.auth import verify_api_key_dependency

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 同步接口（供 backend 项目调用）====================

@router.post("/sync", response_model=Response)
def sync_model_parameter(
    model_parameter: ModelParameterSync, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    同步模型参数配置（新增或更新）
    由 backend 项目调用，当 backend 中的模型参数配置新增或修改时调用此接口
    """
    logger.info(f"开始同步模型参数配置: external_id={model_parameter.external_id}, name={model_parameter.name}")
    
    # 检查是否已存在相同 external_id 的记录
    existing = db.query(ModelParameter).filter(ModelParameter.external_id == model_parameter.external_id).first()
    
    if existing:
        # 更新现有记录
        logger.info(f"发现现有记录，准备更新: id={existing.id}, external_id={model_parameter.external_id}")
        
        # 记录更新前的数据
        old_data = {
            "name": existing.name,
            "type": existing.type,
            "model_type": existing.model_type,
            "required": existing.required
        }
        
        existing.name = model_parameter.name
        existing.type = model_parameter.type
        existing.default_value = model_parameter.default_value
        existing.model_type = model_parameter.model_type
        existing.description = model_parameter.description
        existing.required = model_parameter.required
        existing.validation = model_parameter.validation
        db.commit()
        db.refresh(existing)
        
        logger.info(f"模型参数配置更新成功: id={existing.id}, external_id={model_parameter.external_id}")
        logger.info(f"更新前: {old_data}")
        logger.info(f"更新后: name={existing.name}, type={existing.type}, model_type={existing.model_type}")
        
        return Response(
            success=True,
            message="更新成功",
            data=ModelParameterSchema.model_validate(existing)
        )
    else:
        # 创建新记录
        logger.info(f"创建新的模型参数配置记录: external_id={model_parameter.external_id}")
        
        db_model_parameter = ModelParameter(
            external_id=model_parameter.external_id,
            name=model_parameter.name,
            type=model_parameter.type,
            default_value=model_parameter.default_value,
            model_type=model_parameter.model_type,
            description=model_parameter.description,
            required=model_parameter.required,
            validation=model_parameter.validation
        )
        db.add(db_model_parameter)
        db.commit()
        db.refresh(db_model_parameter)
        
        logger.info(f"模型参数配置创建成功: id={db_model_parameter.id}, external_id={model_parameter.external_id}")
        
        return Response(
            success=True,
            message="创建成功",
            data=ModelParameterSchema.model_validate(db_model_parameter)
        )


@router.delete("/sync/{external_id}", response_model=Response)
def delete_model_parameter_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 删除模型参数配置
    由 backend 项目调用，当 backend 中的模型参数配置删除时调用此接口
    """
    logger.info(f"开始删除模型参数配置: external_id={external_id}")
    
    db_model_parameter = db.query(ModelParameter).filter(ModelParameter.external_id == external_id).first()
    if not db_model_parameter:
        logger.warning(f"模型参数配置未找到: external_id={external_id}")
        raise HTTPException(status_code=404, detail="Model parameter not found")
    
    logger.info(f"找到要删除的模型参数配置: id={db_model_parameter.id}, name={db_model_parameter.name}")
    
    db.delete(db_model_parameter)
    db.commit()
    
    logger.info(f"模型参数配置删除成功: external_id={external_id}")
    
    return Response(
        success=True,
        message="删除成功"
    )


# ==================== 数据读取接口 ====================

@router.get("/list", response_model=Response)
def get_synced_model_parameters(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    model_type: Optional[str] = Query(None, description="按模型类型筛选"),
    parameter_type: Optional[str] = Query(None, description="按参数类型筛选"),
    required: Optional[bool] = Query(None, description="按是否必需筛选"),
    search: Optional[str] = Query(None, description="按名称或描述搜索"),
    db: Session = Depends(get_db)
):
    """
    获取同步的模型参数配置数据集合
    支持分页、类型筛选和搜索功能
    """
    logger.info(f"查询模型参数配置数据: skip={skip}, limit={limit}, model_type={model_type}, parameter_type={parameter_type}, required={required}, search={search}")
    
    try:
        # 构建查询
        query = db.query(ModelParameter)
        
        # 模型类型筛选
        if model_type:
            query = query.filter(ModelParameter.model_type == model_type)
            logger.info(f"应用模型类型筛选: {model_type}")
        
        # 参数类型筛选
        if parameter_type:
            query = query.filter(ModelParameter.type == parameter_type)
            logger.info(f"应用参数类型筛选: {parameter_type}")
        
        # 必需性筛选
        if required is not None:
            query = query.filter(ModelParameter.required == required)
            logger.info(f"应用必需性筛选: {required}")
        
        # 搜索功能
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (ModelParameter.name.ilike(search_filter)) | 
                (ModelParameter.description.ilike(search_filter))
            )
            logger.info(f"应用搜索筛选: {search}")
        
        # 获取总数
        total = query.count()
        logger.info(f"查询到 {total} 条记录")
        
        # 分页查询
        model_parameters = query.offset(skip).limit(limit).all()
        
        # 转换为响应格式
        parameter_data = [ModelParameterSchema.model_validate(param) for param in model_parameters]
        
        logger.info(f"返回 {len(parameter_data)} 条记录")
        
        return Response(
            success=True,
            message=f"查询成功，共 {total} 条记录",
            data={
                "items": parameter_data,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(parameter_data) < total
            }
        )
        
    except Exception as e:
        logger.error(f"查询模型参数配置数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/get/{external_id}", response_model=Response)
def get_model_parameter_by_external_id(
    external_id: int, 
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    根据 external_id 获取单个模型参数配置
    """
    logger.info(f"查询单个模型参数配置: external_id={external_id}")
    
    try:
        model_parameter = db.query(ModelParameter).filter(ModelParameter.external_id == external_id).first()
        
        if not model_parameter:
            logger.warning(f"模型参数配置未找到: external_id={external_id}")
            raise HTTPException(status_code=404, detail="Model parameter not found")
        
        logger.info(f"找到模型参数配置: id={model_parameter.id}, name={model_parameter.name}")
        
        return Response(
            success=True,
            message="查询成功",
            data=ModelParameterSchema.model_validate(model_parameter)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询模型参数配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats", response_model=Response)
def get_model_parameter_stats(
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(verify_api_key_dependency)
):
    """
    获取模型参数配置统计信息
    """
    logger.info("查询模型参数配置统计信息")
    
    try:
        # 总数量
        total_count = db.query(ModelParameter).count()
        
        # 按模型类型统计
        model_type_stats = {}
        model_types = db.query(ModelParameter.model_type).distinct().all()
        for (model_type,) in model_types:
            count = db.query(ModelParameter).filter(ModelParameter.model_type == model_type).count()
            model_type_stats[model_type] = count
        
        # 按参数类型统计
        parameter_type_stats = {}
        parameter_types = db.query(ModelParameter.type).distinct().all()
        for (param_type,) in parameter_types:
            count = db.query(ModelParameter).filter(ModelParameter.type == param_type).count()
            parameter_type_stats[param_type] = count
        
        # 必需参数统计
        required_count = db.query(ModelParameter).filter(ModelParameter.required == True).count()
        optional_count = total_count - required_count
        
        # 最近创建的记录数（最近7天）
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = db.query(ModelParameter).filter(ModelParameter.created_at >= week_ago).count()
        
        stats = {
            "total_count": total_count,
            "model_type_distribution": model_type_stats,
            "parameter_type_distribution": parameter_type_stats,
            "required_count": required_count,
            "optional_count": optional_count,
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
