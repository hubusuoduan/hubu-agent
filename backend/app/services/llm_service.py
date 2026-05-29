"""LLM模型服务 - 用户级工厂模式"""
import asyncio
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from loguru import logger


class LLMService:
    """LLM工厂服务，按 user_id 管理模型实例

    核心思路：
    - user_id 统一从 current_user_id ContextVar 获取（由中间件设置）
    - 请求开始时调 create_for_user()，从数据库读取用户启用的Provider创建模型
    - 请求过程中调 get_model()，从工厂取已创建的模型
    - 请求结束时调 clear_user()，清掉该用户的模型实例
    """

    # 用户级模型缓存 {user_id: ChatOpenAI}
    _user_models: Dict[int, ChatOpenAI] = {}

    @classmethod
    def _get_user_id(cls) -> int:
        """从 ContextVar 获取 user_id"""
        from app.middleware.user_context import current_user_id
        uid = current_user_id.get()
        if uid:
            return uid
        return 0

    @classmethod
    async def _get_enabled_provider(cls, user_id: int) -> Optional[dict]:
        """从数据库获取用户启用的Provider配置"""
        from app.database.dao.llm_provider_dao import LLMProviderDao
        provider = await LLMProviderDao.get_enabled(user_id)
        if not provider:
            return None
        return {
            "id": provider.id,
            "api_key": provider.api_key,
            "base_url": provider.base_url,
            "model": provider.model,
            "enable": provider.enable,
        }

    @classmethod
    async def _ensure_provider(cls, user_id: int) -> dict:
        """确保用户有可用的Provider"""
        provider = await cls._get_enabled_provider(user_id)
        if provider:
            return provider

        raise ValueError(f"用户 {user_id} 没有启用的LLM Provider，请在设置中配置模型供应商")

    @classmethod
    async def create_for_user(cls) -> ChatOpenAI:
        """为用户创建模型实例（请求开始时调用）

        从数据库读取用户启用的Provider配置，创建模型并存入缓存。
        如果已有缓存则先清除再重建，确保配置最新。
        """
        uid = cls._get_user_id()

        # 先清除旧实例
        if uid in cls._user_models:
            del cls._user_models[uid]

        # 从数据库获取用户启用的Provider
        provider = await cls._ensure_provider(uid)

        # 读取用户级配置（同步，从 SettingsFactory 缓存取）
        try:
            from app.services.settings_service import SettingsFactory
            stream_chunk_timeout = SettingsFactory.get(key="LLM_STREAM_CHUNK_TIMEOUT")
        except Exception:
            from app.services.settings_service import _get_default
            stream_chunk_timeout = _get_default("LLM_STREAM_CHUNK_TIMEOUT")

        try:
            model = ChatOpenAI(
                api_key=provider["api_key"],
                base_url=provider["base_url"],
                model=provider["model"],
                temperature=0.7,
                streaming=True,
                stream_usage=True,
                stream_chunk_timeout=stream_chunk_timeout,
            )
            cls._user_models[uid] = model
            logger.info(f"LLM模型创建成功: user={uid}, provider_id={provider['id']}, model={provider['model']}")
            return model
        except Exception as e:
            logger.error(f"LLM模型创建失败 [user={uid}, provider_id={provider['id']}]: {e}")
            raise

    @classmethod
    def get_model(cls) -> ChatOpenAI:
        """获取用户的模型实例

        优先从缓存取，没有则自动创建。
        注意：如果缓存未命中，需要异步创建，请使用 get_model_async。
        """
        uid = cls._get_user_id()
        if uid in cls._user_models:
            return cls._user_models[uid]
        # 同步回退：尝试用事件循环创建
        try:
            loop = asyncio.get_running_loop()
            # 已在异步上下文中，无法直接 await
            raise RuntimeError(f"用户 {uid} 模型未创建，请在异步上下文中先调用 create_for_user")
        except RuntimeError:
            raise

    @classmethod
    async def get_model_async(cls) -> ChatOpenAI:
        """异步获取用户的模型实例，未创建则自动创建"""
        uid = cls._get_user_id()
        if uid not in cls._user_models:
            logger.debug(f"用户 {uid} 模型未创建，自动创建")
            await cls.create_for_user()
        return cls._user_models[uid]

    @classmethod
    def clear_user(cls):
        """清除用户的模型实例（请求结束时调用）"""
        uid = cls._get_user_id()
        if uid in cls._user_models:
            del cls._user_models[uid]
            logger.debug(f"已清除用户 {uid} 的LLM模型实例")

    @classmethod
    async def get_current_provider(cls, user_id: Optional[int] = None) -> dict:
        """获取用户当前启用的Provider信息（API层调用，保留 user_id 参数）"""
        uid = user_id or cls._get_user_id()
        provider = await cls._get_enabled_provider(uid)
        if not provider:
            return {"id": None, "model": "未配置", "enable": False}
        return provider

    @classmethod
    async def get_all_providers(cls, user_id: Optional[int] = None) -> List[dict]:
        """获取用户的所有Provider列表（隐藏api_key，API层调用，保留 user_id 参数）"""
        from app.database.dao.llm_provider_dao import LLMProviderDao
        uid = user_id or cls._get_user_id()
        providers = await LLMProviderDao.list_by_user(uid)
        return [
            {
                "id": p.id,
                "model": p.model,
                "enable": p.enable,
            }
            for p in providers
        ]

    @classmethod
    def reset(cls):
        """重置所有模型实例"""
        cls._user_models.clear()
        logger.info("LLM服务已重置")
