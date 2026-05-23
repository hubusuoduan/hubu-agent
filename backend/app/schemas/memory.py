"""长期记忆相关 Schema"""
from pydantic import BaseModel
from typing import Optional, List


class MemoryResponse(BaseModel):
    """记忆响应"""
    memory_id: str
    content: str
    memory_type: str
    source_dialog_id: Optional[str] = ""
    created_at: Optional[int] = None
    importance: int = 3


class MemoryListResponse(BaseModel):
    """记忆列表响应"""
    total: int
    items: List[MemoryResponse]


class MemoryCreateRequest(BaseModel):
    """手动添加记忆请求"""
    content: str
    memory_type: str = "fact"
    importance: int = 3


class MemoryUpdateRequest(BaseModel):
    """更新记忆请求"""
    content: Optional[str] = None
    memory_type: Optional[str] = None
    importance: Optional[int] = None
