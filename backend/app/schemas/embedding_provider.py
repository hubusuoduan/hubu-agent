"""Embedding Provider 请求/响应 Schema"""
from pydantic import BaseModel
from typing import Optional


class CreateEmbeddingProviderRequest(BaseModel):
    """创建Embedding Provider请求"""
    api_key: str
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "text-embedding-v3"


class UpdateEmbeddingProviderRequest(BaseModel):
    """更新Embedding Provider请求"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class EmbeddingProviderResponse(BaseModel):
    """Embedding Provider响应（简要，隐藏api_key）"""
    id: int
    model: str

    class Config:
        from_attributes = True


class EmbeddingProviderDetailResponse(BaseModel):
    """Embedding Provider详情响应（编辑用，api_key脱敏，base_url完整）"""
    id: int
    api_key: str  # 脱敏后的 api_key
    base_url: str
    model: str

    class Config:
        from_attributes = True
