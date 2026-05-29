"""LLM Provider 数据库模型"""
from sqlmodel import Field, SQLModel
from typing import Optional


class LLMProviderTable(SQLModel, table=True):
    """LLM模型供应商配置表"""
    __tablename__ = "llm_provider"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, description="用户ID，逻辑外键")
    api_key: str = Field(description="API密钥")
    base_url: str = Field(description="API基础URL")
    model: str = Field(description="模型名称，同时作为展示名")
    enable: bool = Field(default=False, description="是否启用，每个用户只能有一个为True")
