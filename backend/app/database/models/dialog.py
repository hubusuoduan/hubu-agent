
"""对话数据模型"""
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, Text, Integer, String

from app.database.models.base import BaseModel


class DialogTable(SQLModel, table=True):
    """对话表"""
    __tablename__ = "dialog"
    __table_args__ = {'comment': '对话表'}

    dialog_id: str = Field(
        default_factory=lambda: uuid4().hex,
        sa_column=Column(String(255), primary_key=True),
        description="对话ID"
    )
    name: str = Field(
        default="新对话",
        max_length=100,
        description="对话名称"
    )
    user_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True, index=True),
        description="用户ID，逻辑关联users表"
    )
    summary: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="对话总结"
    )
    create_time: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(DateTime, nullable=False),
        description="创建时间"
    )
    update_time: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(),
        sa_column=Column(DateTime, nullable=False),
        description="更新时间"
    )
    is_pinned: bool = Field(
        default=False,
        sa_column=Column(Integer, nullable=False, default=0),
        description="是否置顶"
    )
    is_starred: bool = Field(
        default=False,
        sa_column=Column(Integer, nullable=False, default=0),
        description="是否收藏"
    )
    pinned_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
        description="置顶时间"
    )

