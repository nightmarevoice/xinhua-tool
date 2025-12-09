from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None

class Workflow(WorkflowBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    type: str
    status: str
    created_at: datetime
    updated_at: datetime
