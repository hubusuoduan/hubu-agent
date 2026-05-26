
"""聊天相关Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatMessage(BaseModel):
    """聊天消息请求"""
    message: str = Field(min_length=1, description="用户发送的消息")
    dialog_id: Optional[str] = Field(default=None, description="对话ID，为空则自动创建新对话")
    file_content: Optional[str] = Field(default=None, description="文件解析后的内容")


class TruncatedMessage(BaseModel):
    """截断消息保存请求"""
    dialog_id: str = Field(description="对话ID")
    content: str = Field(min_length=1, description="被截断的AI消息内容")

