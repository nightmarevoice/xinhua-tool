from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.chat_log import ChatLog
from app.schemas.chat_log import ChatLogCreate, ChatLog as ChatLogSchema
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ChatLogSchema)
async def create_chat_log(log: ChatLogCreate, db: Session = Depends(get_db)):
    """
    创建聊天日志
    """
    try:
        db_log = ChatLog(
            input_params=log.input_params,
            proprietary_params=log.proprietary_params,
            proprietary_response=log.proprietary_response,
            general_params=log.general_params,
            general_response=log.general_response,
            duration=log.duration
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    except Exception as e:
        logger.error(f"创建聊天日志失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建日志失败: {str(e)}")

@router.get("/", response_model=dict)
async def get_chat_logs(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取聊天日志列表
    """
    try:
        total = db.query(ChatLog).count()
        logs = db.query(ChatLog).order_by(ChatLog.id.desc()).offset(skip).limit(limit).all()
        
        # Convert SQLAlchemy models to Pydantic schemas
        items = [ChatLogSchema.model_validate(log) for log in logs]
        
        return {
            "total": total,
            "items": items
        }
    except Exception as e:
        logger.error(f"获取聊天日志失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")
