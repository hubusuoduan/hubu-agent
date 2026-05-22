"""报告文件数据模型"""
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from sqlalchemy import DateTime, text, Column
from uuid import uuid4

from app.database.models.base import BaseModel


class ReportFormat:
    """报告格式"""
    MARKDOWN = "markdown"
    TXT = "txt"
    HTML = "html"


class ReportStatus:
    """报告状态"""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportTable(BaseModel, table=True):
    """报告文件表"""
    __tablename__ = "report"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    title: str = Field(max_length=256, description="报告标题")
    file_name: str = Field(max_length=256, description="文件名")
    file_format: str = Field(default=ReportFormat.MARKDOWN, max_length=32, description="文件格式")
    file_path: str = Field(default="", max_length=512, description="文件存储路径")
    file_size: int = Field(default=0, description="文件大小(字节)")
    status: str = Field(default=ReportStatus.GENERATING, max_length=32, description="报告状态")
    user_id: str = Field(default="default_user", index=True, max_length=128, description="用户ID")
    dialog_id: str = Field(default="", index=True, max_length=128, description="关联对话ID")

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
