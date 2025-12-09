from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging
import httpx
import os
from datetime import datetime

from app.database import get_db
from app.models.sensitive_word import SensitiveWordGroup as SensitiveWordGroupModel
from app.schemas.sensitive_word import SensitiveWordGroup, SensitiveWordGroupCreate, SensitiveWordGroupUpdate
from app.schemas.common import PaginatedResponse, ApiResponse
from app.utils.response import error_response, success_response, not_found_error
from app.utils.workflow_ctl_sync import get_auth_headers

logger = logging.getLogger(__name__)
router = APIRouter()

# 从环境变量获取 workflow-ctl 服务地址
WORKFLOW_CTL_BASE_URL = os.getenv("WORKFLOW_CTL_BASE_URL", "http://localhost:8889")

@router.get("/list", response_model=PaginatedResponse)
async def get_sensitive_word_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取敏感词组列表"""
    query = db.query(SensitiveWordGroupModel)
    
    if search:
        query = query.filter(
            SensitiveWordGroupModel.name.contains(search) | 
            SensitiveWordGroupModel.description.contains(search)
        )
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    from app.schemas.common import PaginatedData
    
    return PaginatedResponse[SensitiveWordGroup](
        data=PaginatedData[SensitiveWordGroup](
            items=[SensitiveWordGroup.from_orm(item) for item in items],
            total=total,
            page=page,
            page_size=page_size
        )
    )

@router.get("/get", response_model=ApiResponse)
async def get_sensitive_word_group(
    group_id: str = Query(..., description="Sensitive Word Group ID"), 
    db: Session = Depends(get_db)
):
    """获取单个敏感词组"""
    group = db.query(SensitiveWordGroupModel).filter(SensitiveWordGroupModel.id == group_id).first()
    if not group:
        return not_found_error("Sensitive Word Group")
    
    return success_response("获取敏感词组成功", SensitiveWordGroup.from_orm(group))

@router.post("/create", response_model=ApiResponse)
async def create_sensitive_word_group(
    group: SensitiveWordGroupCreate, 
    db: Session = Depends(get_db)
):
    """创建敏感词组"""
    # 验证敏感词列表不为空
    if not group.words or len(group.words) == 0:
        return error_response("敏感词列表不能为空")
    
    db_group = SensitiveWordGroupModel(
        id=str(uuid.uuid4()),
        name=group.name,
        description=group.description,
        words=group.words
    )
    
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    logger.info(f"敏感词组创建成功: group_id={db_group.id}, name={db_group.name}")
    
    # 调用 workflow-ctl 添加违禁词
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{WORKFLOW_CTL_BASE_URL}/api/sensitive-words/add",
                json={"words": group.words},
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"违禁词已同步到 workflow-ctl: {result}")
            else:
                logger.warning(f"同步违禁词到 workflow-ctl 失败: status={response.status_code}, body={response.text}")
    except Exception as e:
        logger.error(f"调用 workflow-ctl 添加违禁词失败: {str(e)}")
        # 不影响主流程，继续返回成功
    
    return success_response("敏感词组创建成功", SensitiveWordGroup.from_orm(db_group))

@router.put("/update", response_model=ApiResponse)
async def update_sensitive_word_group(
    group_id: str = Query(..., description="Sensitive Word Group ID"),
    group: SensitiveWordGroupUpdate = Body(..., description="更新数据"),
    db: Session = Depends(get_db)
):
    """更新敏感词组"""
    db_group = db.query(SensitiveWordGroupModel).filter(SensitiveWordGroupModel.id == group_id).first()
    if not db_group:
        return not_found_error("Sensitive Word Group")
    
    # 更新字段
    update_data = group.model_dump(exclude_unset=True)
    if not update_data:
        return error_response("没有提供要更新的字段")
    
    # 如果更新了敏感词列表，验证不为空
    if 'words' in update_data and (not update_data['words'] or len(update_data['words']) == 0):
        return error_response("敏感词列表不能为空")
    
    logger.info(f"开始更新敏感词组: group_id={group_id}, 更新字段: {list(update_data.keys())}")
    
    # 如果更新了敏感词列表，需要先删除旧的，再添加新的
    old_words = db_group.words if 'words' in update_data else None
    new_words = update_data.get('words') if 'words' in update_data else None
    
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db_group.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_group)
    
    logger.info(f"敏感词组更新成功: group_id={group_id}")
    
    # 如果更新了敏感词列表，同步到 workflow-ctl
    if old_words is not None and new_words is not None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. 先删除旧的违禁词
                if old_words:
                    delete_response = await client.request(
                        method="DELETE",
                        url=f"{WORKFLOW_CTL_BASE_URL}/api/sensitive-words/delete",
                        json={"words": old_words},
                        headers=get_auth_headers()
                    )
                    
                    if delete_response.status_code == 200:
                        logger.info(f"旧违禁词已从 workflow-ctl 删除: {len(old_words)} 个")
                    else:
                        logger.warning(f"删除旧违禁词失败: status={delete_response.status_code}")
                
                # 2. 再添加新的违禁词
                if new_words:
                    add_response = await client.post(
                        f"{WORKFLOW_CTL_BASE_URL}/api/sensitive-words/add",
                        json={"words": new_words},
                        headers=get_auth_headers()
                    )
                    
                    if add_response.status_code == 200:
                        logger.info(f"新违禁词已同步到 workflow-ctl: {len(new_words)} 个")
                    else:
                        logger.warning(f"添加新违禁词失败: status={add_response.status_code}")
        except Exception as e:
            logger.error(f"同步违禁词到 workflow-ctl 失败: {str(e)}")
            # 不影响主流程
    
    return success_response("敏感词组更新成功", SensitiveWordGroup.from_orm(db_group))

@router.delete("/delete", response_model=ApiResponse)
async def delete_sensitive_word_group(
    group_id: str = Query(..., description="Sensitive Word Group ID"), 
    db: Session = Depends(get_db)
):
    """删除敏感词组"""
    db_group = db.query(SensitiveWordGroupModel).filter(SensitiveWordGroupModel.id == group_id).first()
    if not db_group:
        return not_found_error("Sensitive Word Group")
    
    # 保存要删除的词列表，用于同步到 workflow-ctl
    words_to_delete = db_group.words
    
    db.delete(db_group)
    db.commit()
    
    logger.info(f"敏感词组删除成功: group_id={group_id}")
    
    # 调用 workflow-ctl 删除违禁词
    if words_to_delete:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.request(
                    method="DELETE",
                    url=f"{WORKFLOW_CTL_BASE_URL}/api/sensitive-words/delete",
                    json={"words": words_to_delete},
                    headers=get_auth_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"违禁词已从 workflow-ctl 删除: {result}")
                else:
                    logger.warning(f"从 workflow-ctl 删除违禁词失败: status={response.status_code}, body={response.text}")
        except Exception as e:
            logger.error(f"调用 workflow-ctl 删除违禁词失败: {str(e)}")
            # 不影响主流程
    
    return success_response("敏感词组删除成功")

@router.get("/stats", response_model=ApiResponse)
async def get_sensitive_word_stats(db: Session = Depends(get_db)):
    """获取敏感词组统计信息"""
    total_count = db.query(SensitiveWordGroupModel).count()
    return success_response("获取统计信息成功", {"total_count": total_count})








