"""数据库基础模型"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, text


class BaseModel(SQLModel):
    """基础模型类"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    create_time: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(),
        sa_type=DateTime,
        nullable=False,
        description="创建时间"
    )
    update_time: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(),
        sa_type=DateTime,
        nullable=False,
        description="更新时间"
    )
