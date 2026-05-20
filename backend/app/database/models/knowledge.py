"""知识库数据模型"""
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from sqlalchemy import DateTime, text, Column
from uuid import uuid4

from app.database.models.base import BaseModel


def get_knowledge_id():
    """生成知识库ID"""
    return f"k_{uuid4().hex[:16]}"


class KnowledgeTable(BaseModel, table=True):
    """知识库表"""
    __tablename__ = "knowledge"
    
    id: str = Field(default_factory=get_knowledge_id, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=128, description="知识库名称")
    description: Optional[str] = Field(max_length=1024, default=None, description="知识库描述")
    user_id: Optional[str] = Field(index=True, max_length=128, default=None, description="用户ID")
    
    # 覆盖时间字段，使用数据库默认值
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )
    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP'),
            onupdate=text('CURRENT_TIMESTAMP')
        ),
        description="更新时间"
    )
