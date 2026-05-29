"""Token 使用量统计模型"""
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date
from uuid import uuid4
from sqlalchemy import Column, String, BigInteger, Date, UniqueConstraint


class UsageStatsTable(SQLModel, table=True):
    """Token 使用量统计表（同一天同模型同用户合并为一条记录，累加 token）"""
    __tablename__ = "usage_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "model", "stat_date", name="uq_user_model_date"),
        {"comment": "Token使用量统计表"},
    )

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
    stat_date: Optional[date] = Field(
        default_factory=date.today,
        sa_column=Column(Date, nullable=False, index=True),
        description="统计日期"
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
    request_count: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False, default=0),
        description="请求次数"
    )
