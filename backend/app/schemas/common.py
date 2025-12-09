from pydantic import BaseModel
from typing import List, Any, Optional, TypeVar, Generic

T = TypeVar('T')

class PaginatedData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

class PaginatedResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: PaginatedData[T]

class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    success: bool = True
    data: Optional[T] = None
