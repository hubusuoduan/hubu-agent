"""用户自建 Agent 模型"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text


class UserAgentTable(SQLModel, table=True):
    __tablename__ = "user_agent"
    __table_args__ = {'comment': '用户自建Agent索引表'}
    """用户自建 Agent 索引表

    详细配置（prompt、工具列表等）存放在 md 文件中，
    此表只存索引信息和 Supervisor 路由所需的简短描述。
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        ...,
        sa_column=Column(Integer, nullable=False, index=True),
        description="所属用户ID"
    )
    name: str = Field(
        ...,
        sa_column=Column(String(64), nullable=False),
        description="Agent名称，如 translator"
    )
    display_name: str = Field(
        default="",
        sa_column=Column(String(128), nullable=False, default=""),
        description="显示名，如 翻译官"
    )
    description: str = Field(
        default="",
        sa_column=Column(String(512), nullable=False, default=""),
        description="简短描述，给 Supervisor 路由用"
    )
    agent_path: str = Field(
        ...,
        sa_column=Column(String(512), nullable=False),
        description="AGENT.md 相对路径，如 custom/1/translator/AGENT.md"
    )
    enabled: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, default=1),
        description="是否启用 1=启用 0=禁用"
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
