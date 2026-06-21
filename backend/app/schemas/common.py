from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, List, Any

T = TypeVar('T')

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "page": 1,
            "page_size": 20,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
    })

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

class ResponseModel(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "Success"
    data: Any = None
    timestamp: str = None
