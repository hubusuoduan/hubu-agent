
"""对话相关Schema"""
from pydantic import BaseModel, Field


class CreateDialogRequest(BaseModel):
    """创建对话请求"""
    name: str = Field(default="新对话", max_length=100, description="对话名称")


class UpdateDialogNameRequest(BaseModel):
    """更新对话名称请求"""
    name: str = Field(min_length=1, max_length=100, description="新名称")


class UpdateDialogPinRequest(BaseModel):
    """更新对话置顶状态请求"""
    is_pinned: bool = Field(description="是否置顶")


class UpdateDialogStarRequest(BaseModel):
    """更新对话收藏状态请求"""
    is_starred: bool = Field(description="是否收藏")

