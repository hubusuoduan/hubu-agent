"""Token 使用量统计模型"""
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime, String, BigInteger

from app.database.models.base import BaseModel


class UsageStatsTable(BaseModel, table=True):
    """Token 使用量统计表"""
    __tablename__ = "usage_stats"
    __table_args__ = {"comment": "Token使用量统计表"}

    id: str = Field(
        default_factory=lambda: uuid4().hex,
        primary_key=True,
        description="记录ID"
    )
    user_id: str = Field(
        max_length=255,
        sa_column=Column(String(255), nullable=False, index=True),
        description="用户ID"
    )
    model: str = Field(
        max_length=255,
        sa_column=Column(String(255), nullable=False, default=""),
        description="模型名称"
    )
    input_tokens: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
        description="输入Token数"
    )
    output_tokens: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
        description="输出Token数"
    )
