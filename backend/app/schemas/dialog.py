
"""对话相关Schema"""
from pydantic import BaseModel, Field


class CreateDialogRequest(BaseModel):
    """创建对话请求"""
    name: str = Field(default="新对话", max_length=100, description="对话名称")


class UpdateDialogNameRequest(BaseModel):
    """更新对话名称请求"""
    name: str = Field(min_length=1, max_length=100, description="新名称")

