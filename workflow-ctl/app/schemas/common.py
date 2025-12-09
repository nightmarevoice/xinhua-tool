from pydantic import BaseModel
from typing import Any, Optional

class Response(BaseModel):
    success: bool
    message: str = ""
    data: Any = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None














