"""用户自建 Agent 相关 Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserAgentCreate(BaseModel):
    """创建用户自建 Agent 请求"""
    name: str = Field(..., description="Agent名称，如 translator", max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    display_name: str = Field(..., description="显示名，如 翻译官", max_length=128)
    description: str = Field(..., description="简短描述，给 Supervisor 路由用", max_length=512)
    system_prompt: str = Field(..., description="System Prompt 正文")
    tools: List[str] = Field(default=[], description="可用工具名称列表，如 ['web_search', 'file_read']")


class UserAgentUpdate(BaseModel):
    """更新用户自建 Agent 请求"""
    display_name: Optional[str] = Field(default=None, description="显示名", max_length=128)
    description: Optional[str] = Field(default=None, description="简短描述", max_length=512)
    system_prompt: Optional[str] = Field(default=None, description="System Prompt 正文")
    tools: Optional[List[str]] = Field(default=None, description="可用工具名称列表")
    enabled: Optional[int] = Field(default=None, description="是否启用 1=启用 0=禁用")


class UserAgentResponse(BaseModel):
    """用户自建 Agent 响应"""
    id: int
    user_id: int
    name: str
    display_name: str
    description: str
    tools: List[str] = []
    system_prompt: str = ""
    enabled: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class UserAgentListResponse(BaseModel):
    """用户自建 Agent 列表响应"""
    total: int
    items: List[UserAgentResponse]


class ToolInfo(BaseModel):
    """工具信息（供前端选择工具时使用）"""
    name: str
    description: str


class ToolListResponse(BaseModel):
    """可用工具列表响应"""
    tools: List[ToolInfo]
