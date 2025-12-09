from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ChatLogBase(BaseModel):
    input_params: Dict[str, Any]
    proprietary_params: Optional[Dict[str, Any]] = None
    proprietary_response: Optional[str] = None
    general_params: Optional[Dict[str, Any]] = None
    general_response: Optional[str] = None
    duration: float

class ChatLogCreate(ChatLogBase):
    pass

class ChatLog(ChatLogBase):
    id: int
    call_time: datetime

    class Config:
        from_attributes = True
