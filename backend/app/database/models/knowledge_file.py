"""知识库文件数据模型"""
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from sqlalchemy import DateTime, text, Column
from uuid import uuid4

from app.database.models.base import BaseModel


class FileStatus:
    """文件处理状态"""
    FAIL = "fail"
    PROCESSING = "processing"
    SUCCESS = "success"


class KnowledgeFileTable(BaseModel, table=True):
    """知识库文件表"""
    __tablename__ = "knowledge_file"
    
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    file_name: str = Field(index=True, max_length=256, description="文件名")
    knowledge_id: str = Field(index=True, max_length=128, description="知识库ID")
    status: str = Field(default=FileStatus.SUCCESS, max_length=32, description="文件解析状态")
    user_id: str = Field(index=True, max_length=128, description="用户ID")
    oss_url: str = Field(default="", max_length=512, description="文件存储路径")
    file_size: int = Field(default=0, description="文件大小(字节)")
    
    # 覆盖时间字段
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
