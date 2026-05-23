
"""对话导出相关Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ExportFormat(str, Enum):
    """导出格式"""
    markdown = "markdown"


class ExportRange(str, Enum):
    """导出范围"""
    all = "all"
    recent = "recent"
    custom = "custom"


class ExportDialogRequest(BaseModel):
    """对话导出请求"""
    format: ExportFormat = Field(
        default=ExportFormat.markdown,
        description="导出格式：markdown 或 pdf"
    )
    range: ExportRange = Field(
        default=ExportRange.all,
        description="导出范围：all(全部)、recent(最近N条)、custom(自定义范围)"
    )
    recent_count: Optional[int] = Field(
        default=None,
        description="当range=recent时，指定最近的消息条数"
    )
    start_index: Optional[int] = Field(
        default=None,
        description="当range=custom时，起始消息索引（从0开始）"
    )
    end_index: Optional[int] = Field(
        default=None,
        description="当range=custom时，结束消息索引（不包含）"
    )
