"""LLM模型服务 - 支持多模型切换"""
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from loguru import logger

from app.config import settings


class LLMService:
    """LLM服务类，管理多模型切换

    内部维护：
    - _providers: 所有可用的模型Provider配置
    - _current_provider_id: 当前使用的Provider ID
    - _models: 已实例化的模型缓存 {provider_id: ChatOpenAI}
    """

    _providers: List[dict] = []
    _current_provider_id: str = ""
    _models: Dict[str, ChatOpenAI] = {}

    @classmethod
    def _init_providers(cls):
        """初始化Provider配置（懒加载）"""
        if not cls._providers:
            cls._providers = settings.model_providers
            cls._current_provider_id = settings.default_provider_id
            logger.info(f"LLM Provider 初始化: {[p['id'] for p in cls._providers]}, 当前: {cls._current_provider_id}")

    @classmethod
    def get_model(cls) -> ChatOpenAI:
        """获取当前模型实例（无参，直接返回当前选中的模型）"""
        cls._init_providers()
        provider_id = cls._current_provider_id

        if provider_id not in cls._models:
            cls._create_model(provider_id)

        return cls._models[provider_id]

    @classmethod
    def _create_model(cls, provider_id: str) -> ChatOpenAI:
        """根据provider_id创建模型实例"""
        provider = cls._get_provider(provider_id)
        if not provider:
            raise ValueError(f"未找到模型配置: {provider_id}")

        try:
            model = ChatOpenAI(
                api_key=provider["api_key"],
                base_url=provider["base_url"],
                model=provider["model"],
                temperature=provider.get("temperature", 0.7),
                streaming=True,
                stream_usage=True,
                stream_chunk_timeout=settings.LLM_STREAM_CHUNK_TIMEOUT,
            )
            cls._models[provider_id] = model
            logger.info(f"LLM模型创建成功: [{provider_id}] {provider['model']}")
            return model
        except Exception as e:
            logger.error(f"LLM模型创建失败 [{provider_id}]: {e}")
            raise

    @classmethod
    def _get_provider(cls, provider_id: str) -> Optional[dict]:
        """根据ID获取Provider配置"""
        cls._init_providers()
        for p in cls._providers:
            if p["id"] == provider_id:
                return p
        return None

    @classmethod
    def get_current_provider(cls) -> dict:
        """获取当前Provider信息"""
        cls._init_providers()
        provider = cls._get_provider(cls._current_provider_id)
        if not provider:
            return {"id": "default", "name": "未知", "model": "unknown", "is_default": True}
        return provider

    @classmethod
    def get_all_providers(cls) -> List[dict]:
        """获取所有Provider列表（隐藏api_key）"""
        cls._init_providers()
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "model": p["model"],
                "is_default": p.get("is_default", False),
                "is_current": p["id"] == cls._current_provider_id
            }
            for p in cls._providers
        ]

    @classmethod
    def switch_provider(cls, provider_id: str) -> dict:
        """切换当前模型Provider"""
        cls._init_providers()
        provider = cls._get_provider(provider_id)
        if not provider:
            raise ValueError(f"未找到模型配置: {provider_id}")

        old_id = cls._current_provider_id
        cls._current_provider_id = provider_id

        # 预创建模型实例
        if provider_id not in cls._models:
            cls._create_model(provider_id)

        logger.info(f"LLM模型切换: {old_id} -> {provider_id}")
        return cls.get_current_provider()

    @classmethod
    def reset(cls):
        """重置所有模型实例和配置"""
        cls._models.clear()
        cls._providers = []
        cls._current_provider_id = ""
        logger.info("LLM服务已重置")
