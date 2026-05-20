"""对话数据模型"""
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, Text, text

from app.database.models.base import BaseModel


class DialogTable(BaseModel, table=True):
    """对话表"""
    __tablename__ = "dialog"
    __table_args__ = {'comment': '对话表'}

    dialog_id: str = Field(
        default_factory=lambda: uuid4().hex,
        primary_key=True,
        description="对话ID"
    )
    name: str = Field(
        default="新对话",
        max_length=100,
        description="对话名称"
    )
    user_id: str = Field(
        default="default_user",
        max_length=100,
        description="用户ID"
    )
    summary: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="对话总结"
    )
