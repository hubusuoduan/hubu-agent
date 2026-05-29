"""Embedding Provider 数据库模型"""
from sqlmodel import Field, SQLModel
from typing import Optional


class EmbeddingProviderTable(SQLModel, table=True):
    """Embedding模型供应商配置表（每用户仅一条记录）"""
    __tablename__ = "embedding_provider"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, description="用户ID，逻辑外键")
    api_key: str = Field(description="API密钥")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", description="API基础URL")
    model: str = Field(default="text-embedding-v3", description="Embedding模型名称")
