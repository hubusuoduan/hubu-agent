"""对话历史数据模型"""
from sqlmodel import Field, SQLModel
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, Text, JSON, text

from app.database.models.base import BaseModel


class HistoryTable(BaseModel, table=True):
    """对话历史表"""
    __tablename__ = "history"
    __table_args__ = {'comment': '对话历史表'}

    id: str = Field(
        default_factory=lambda: uuid4().hex,
        primary_key=True,
        description="消息ID"
    )
    dialog_id: str = Field(
        max_length=100,
        description="对话ID"
    )
    role: str = Field(
        max_length=20,
        description="角色：user/assistant/system"
    )
    content: str = Field(
        sa_column=Column(Text),
        description="消息内容"
    )
    token_usage: int = Field(
        default=0,
        description="Token使用量"
    )
