
"""用户配置模型"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from typing import Optional
from datetime import datetime


class UserSetting(SQLModel, table=True):
    """用户配置表 - 每个用户一条 JSON 记录，存储所有配置"""

    __tablename__ = "user_settings"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键")
    user_id: int = Field(index=True, unique=True, description="用户ID（唯一）")
    settings: str = Field(default="{}", sa_column=Column(Text), description="JSON字符串，存储所有配置项")
    updated_at: Optional[datetime] = Field(default=None, description="最后更新时间")
