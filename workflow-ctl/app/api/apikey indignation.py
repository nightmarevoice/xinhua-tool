from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.502.orm import Session
from app.database.database import get_db
from app.models.apikey import ApiKey
from app.schemas.apikey import ApiKeySync, ApiKey as ApiKeySchema
from app.schemas.common import Response

router = APIRouter()


# ==================== 同步接口（供 backend 项目调用）====================

@router.post("/sync", response_model=Response)
def sync_apikey(apikey: ApiKeySync, db: Session = Depends(get_db)):
    """
    同步 API Key（新增或更新）
    由 backend 项目调用，当 backend 中的 API Key 新增或修改时调用此接口
    """
    # 检查是否已存在相同 external_id 的记录
    existing = db.query(ApiKey).filter(ApiKey.external_id == apikey.external_id).first()
    
    if existing:
        # 更新现有记录
        existing.name = apikey.name
        existing.description = apikey.description
        existing.key = apikey.key
        existing.status = apikey.status
        db.commit()
        db.refresh(existing)
        
        return Response(
            success=True,
            message="更新成功",
            data=ApiKeySchema.model_validate(existing)
        )
    else:
        # 创建新记录
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
        
        return Response(
            success=True,
            message="创建成功",
            data=ApiKeySchema.model_validate(db_apikey)
        )


@router.delete("/sync/{external_id}", response_model=Response)
def delete_apikey_by_external_id(external_id: int, db: Session = Depends(get_db)):
    """
    根据 external_id 删除 API Key
    由 backend 项目调用，当 backend 中的 API Key 删除时调用此接口
    """
    db_apikey = db.query(ApiKey).filter(ApiKey.external_id == external_id).first()
    if not db_apikey:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    db.delete(db_apikey)
    db.commit()
    
    return Response(
        success=True,
        message="删除成功"
    )







