"""LLM Provider 请求/响应 Schema"""
from pydantic import BaseModel
from typing import Optional


class CreateProviderRequest(BaseModel):
    """创建Provider请求"""
    api_key: str
    base_url: str
    model: str
    enable: bool = False


class UpdateProviderRequest(BaseModel):
    """更新Provider请求"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    enable: Optional[bool] = None


class ProviderResponse(BaseModel):
    """Provider响应"""
    id: int
    user_id: int
    api_key: str
    base_url: str
    model: str
    enable: bool

    class Config:
        from_attributes = True


class ProviderBriefResponse(BaseModel):
    """Provider简要响应（隐藏api_key）"""
    id: int
    model: str
    enable: bool

    class Config:
        from_attributes = True


class ProviderDetailResponse(BaseModel):
    """Provider详情响应（编辑时使用，api_key脱敏，base_url完整）"""
    id: int
    api_key: str  # 脱敏后的 api_key，如 sk-****1234
    base_url: str
    model: str
    enable: bool

    class Config:
        from_attributes = True
