
"""对话相关Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateDialogRequest(BaseModel):
    """创建对话请求"""
    name: str = Field(default="新对话", max_length=100, description="对话名称")


class UpdateDialogNameRequest(BaseModel):
    """更新对话名称请求"""
    name: str = Field(min_length=1, max_length=100, description="新名称")


class DialogResponse(BaseModel):
    """对话响应"""
    dialog_id: str = Field(description="对话ID")
    name: str = Field(description="对话名称")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    summary: Optional[str] = Field(default=None, description="对话总结")
    create_time: Optional[str] = Field(default=None, description="创建时间")
    update_time: Optional[str] = Field(default=None, description="更新时间")


class DialogListResponse(BaseModel):
    """对话列表响应"""
    dialogs: List[DialogResponse] = Field(description="对话列表")
    total: int = Field(description="总数")


class HistoryMessageResponse(BaseModel):
    """历史消息响应"""
    role: str = Field(description="角色：user/assistant/system")
    content: str = Field(description="消息内容")
    create_time: Optional[str] = Field(default=None, description="创建时间")


class DialogHistoryResponse(BaseModel):
    """对话历史响应"""
    dialog_id: str = Field(description="对话ID")
    messages: List[HistoryMessageResponse] = Field(description="消息列表")
    total: int = Field(description="消息总数")
