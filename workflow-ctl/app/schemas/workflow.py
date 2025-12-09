from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: str
    config: Dict[str, Any]
    status: Optional[str] = "active"  # active, inactive

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class Workflow(WorkflowBase):
    id: int
    external_id: Optional[int] = None
    backend_id: Optional[str] = None  # backend 系统的原始字符串 ID（UUID）
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# 同步接口使用的 Schema
class WorkflowSync(BaseModel):
    """用于 backend 同步的 Workflow Schema"""
    external_id: int  # backend 系统的 ID（哈希值）
    backend_id: Optional[str] = None  # backend 系统的原始字符串 ID（UUID）
    name: str
    description: Optional[str] = None
    workflow_type: str
    config: Dict[str, Any]
    status: Optional[str] = "active"  # active, inactive


