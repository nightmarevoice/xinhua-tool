from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from app.database import get_db
from app.models.llm_provider import LLMProvider as LLMProviderModel
from app.schemas.llm_provider import LLMProvider, LLMProviderCreate, LLMProviderUpdate
from app.schemas.common import PaginatedResponse, ApiResponse
from app.utils.response import error_response, success_response, not_found_error
from app.utils.workflow_ctl_sync import sync_llm_provider_to_workflow_ctl, delete_from_workflow_ctl
from app.utils.crypto import encrypt_api_key, mask_api_key, is_encrypted

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/list", response_model=PaginatedResponse)
async def get_llm_providers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取LLM Provider列表"""
    query = db.query(LLMProviderModel)
    
    if search:
        query = query.filter(
            LLMProviderModel.name.contains(search) | 
            LLMProviderModel.default_model_name.contains(search)
        )
    
    if provider:
        query = query.filter(LLMProviderModel.provider == provider)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    from app.schemas.common import PaginatedData
    
    # 将SQLAlchemy模型转换为Pydantic模型，并对 API 密钥进行脱敏
    llm_providers = []
    for item in items:
        provider = LLMProvider.from_orm(item)
        # 脱敏显示 API 密钥
        if provider.api_key:
            provider.api_key = mask_api_key(provider.api_key)
        llm_providers.append(provider)
    
    return PaginatedResponse[LLMProvider](
        data=PaginatedData[LLMProvider](
            items=llm_providers,
            total=total,
            page=page,
            page_size=page_size
        )
    )

@router.get("/get", response_model=ApiResponse)
async def get_llm_provider(provider_id: int = Query(..., description="Provider ID"), db: Session = Depends(get_db)):
    """获取单个LLM Provider"""
    provider = db.query(LLMProviderModel).filter(LLMProviderModel.id == provider_id).first()
    if not provider:
        return not_found_error("LLM Provider不存在")
    
    # 将SQLAlchemy模型转换为Pydantic模型
    provider_schema = LLMProvider.from_orm(provider)
    # 脱敏显示 API 密钥
    if provider_schema.api_key:
        provider_schema.api_key = mask_api_key(provider_schema.api_key)
    return success_response("获取LLM Provider成功", provider_schema)

@router.post("/create", response_model=ApiResponse)
async def create_llm_provider(provider: LLMProviderCreate, db: Session = Depends(get_db)):
    """创建LLM Provider"""
    # 将ModelConfiguration对象转换为字典
    model_configs = None
    if provider.model_configurations:
        model_configs = [config.dict() for config in provider.model_configurations]
    
    # 加密 API 密钥
    encrypted_api_key = encrypt_api_key(provider.api_key) if provider.api_key else None
    
    db_provider = LLMProviderModel(
        name=provider.name,
        provider=provider.provider,
        api_key=encrypted_api_key,  # 存储加密后的密钥
        api_base=provider.api_base,
        api_version=provider.api_version,
        custom_config=provider.custom_config,
        default_model_name=provider.default_model_name,
        fast_default_model_name=provider.fast_default_model_name,
        deployment_name=provider.deployment_name,
        default_vision_model=provider.default_vision_model,
        model_configurations=model_configs,
        is_default_provider=provider.is_default_provider,
        is_default_vision_provider=provider.is_default_vision_provider
    )
    
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    
    # 同步到 workflow-ctl
    await sync_llm_provider_to_workflow_ctl(
        external_id=db_provider.id,
        name=db_provider.name,
        provider=db_provider.provider,
        api_key=db_provider.api_key,
        api_base=db_provider.api_base,
        api_version=db_provider.api_version,
        custom_config=db_provider.custom_config,
        default_model_name=db_provider.default_model_name,
        fast_default_model_name=db_provider.fast_default_model_name,
        deployment_name=db_provider.deployment_name,
        default_vision_model=db_provider.default_vision_model,
        model_configurations=db_provider.model_configurations,
        category=db_provider.category,
        is_default_provider=db_provider.is_default_provider,
        is_default_vision_provider=db_provider.is_default_vision_provider
    )
    
    # 将SQLAlchemy模型转换为Pydantic模型
    provider_schema = LLMProvider.from_orm(db_provider)
    return success_response("LLM Provider创建成功", provider_schema)

@router.put("/update", response_model=ApiResponse)
async def update_llm_provider(
    provider_id: int = Query(..., description="Provider ID"),
    provider: LLMProviderUpdate = Body(None, description="更新数据"),
    db: Session = Depends(get_db)
):
    """更新LLM Provider"""
    db_provider = db.query(LLMProviderModel).filter(LLMProviderModel.id == provider_id).first()
    if not db_provider:
        return not_found_error("LLM Provider不存在")
    
    # 更新字段
    if provider is None:
        return error_response("请提供要更新的字段")
    
    update_data = provider.model_dump(exclude_unset=True)
    if not update_data:
        return error_response("没有提供要更新的字段")
    
    # 处理model_configurations字段的序列化
    if 'model_configurations' in update_data and update_data['model_configurations'] is not None:
        # 如果 model_configurations 是对象列表，转换为字典列表
        if update_data['model_configurations']:
            configs = []
            for config in update_data['model_configurations']:
                if hasattr(config, 'dict'):
                    configs.append(config.dict())
                elif isinstance(config, dict):
                    configs.append(config)
                else:
                    configs.append(dict(config))
            update_data['model_configurations'] = configs
    
    # 处理 API 密钥的加密
    if 'api_key' in update_data and update_data['api_key']:
        # 如果 API 密钥不是脱敏格式（包含****），则是新密钥需要加密
        if '****' not in update_data['api_key']:
            update_data['api_key'] = encrypt_api_key(update_data['api_key'])
        else:
            # 如果是脱敏格式，说明前端没有修改，保持原值不变
            update_data.pop('api_key')
    
    for field, value in update_data.items():
        setattr(db_provider, field, value)
    
    db_provider.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_provider)
    
    # 同步到 workflow-ctl
    await sync_llm_provider_to_workflow_ctl(
        external_id=db_provider.id,
        name=db_provider.name,
        provider=db_provider.provider,
        api_key=db_provider.api_key,
        api_base=db_provider.api_base,
        api_version=db_provider.api_version,
        custom_config=db_provider.custom_config,
        default_model_name=db_provider.default_model_name,
        fast_default_model_name=db_provider.fast_default_model_name,
        deployment_name=db_provider.deployment_name,
        default_vision_model=db_provider.default_vision_model,
        model_configurations=db_provider.model_configurations,
        category=db_provider.category,
        is_default_provider=db_provider.is_default_provider,
        is_default_vision_provider=db_provider.is_default_vision_provider
    )
    
    # 将SQLAlchemy模型转换为Pydantic模型
    provider_schema = LLMProvider.from_orm(db_provider)
    return success_response("LLM Provider更新成功", provider_schema)

@router.delete("/delete", response_model=ApiResponse)
async def delete_llm_provider(provider_id: int = Query(..., description="Provider ID"), db: Session = Depends(get_db)):
    """删除LLM Provider"""
    provider = db.query(LLMProviderModel).filter(LLMProviderModel.id == provider_id).first()
    if not provider:
        return not_found_error("LLM Provider不存在")
    
    db.delete(provider)
    db.commit()
    
    # 同步删除到 workflow-ctl
    await delete_from_workflow_ctl("llm-providers", provider_id)
    
    return success_response("LLM Provider删除成功", None)
