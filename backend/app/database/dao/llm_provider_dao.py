"""LLM Provider DAO 层"""
from typing import List, Optional
from sqlmodel import select
from loguru import logger

from app.database.engine import async_engine
from app.database.models.llm_provider import LLMProviderTable
from sqlmodel.ext.asyncio.session import AsyncSession


class LLMProviderDao:
    """LLM Provider 数据访问对象"""

    @classmethod
    async def get_by_id(cls, provider_id: int) -> Optional[LLMProviderTable]:
        """根据ID获取Provider"""
        async with AsyncSession(async_engine) as session:
            statement = select(LLMProviderTable).where(LLMProviderTable.id == provider_id)
            result = await session.execute(statement)
            return result.scalars().first()

    @classmethod
    async def get_by_id_and_user(cls, provider_id: int, user_id: int) -> Optional[LLMProviderTable]:
        """根据ID和用户ID获取Provider（安全校验）"""
        async with AsyncSession(async_engine) as session:
            statement = select(LLMProviderTable).where(
                LLMProviderTable.id == provider_id,
                LLMProviderTable.user_id == user_id
            )
            result = await session.execute(statement)
            return result.scalars().first()

    @classmethod
    async def list_by_user(cls, user_id: int) -> List[LLMProviderTable]:
        """获取用户的所有Provider列表"""
        async with AsyncSession(async_engine) as session:
            statement = select(LLMProviderTable).where(LLMProviderTable.user_id == user_id)
            result = await session.execute(statement)
            return list(result.scalars().all())

    @classmethod
    async def get_enabled(cls, user_id: int) -> Optional[LLMProviderTable]:
        """获取用户启用的Provider（enable=True）"""
        async with AsyncSession(async_engine) as session:
            statement = select(LLMProviderTable).where(
                LLMProviderTable.user_id == user_id,
                LLMProviderTable.enable == True
            )
            result = await session.execute(statement)
            return result.scalars().first()

    @classmethod
    async def create(cls, provider: LLMProviderTable) -> LLMProviderTable:
        """创建Provider，如果enable=True则先关闭同用户其他Provider"""
        async with AsyncSession(async_engine) as session:
            if provider.enable:
                await cls._disable_all(session, provider.user_id)
            session.add(provider)
            await session.commit()
            await session.refresh(provider)
            return provider

    @classmethod
    async def update(cls, provider_id: int, user_id: int, **kwargs) -> Optional[LLMProviderTable]:
        """更新Provider，如果enable=True则先关闭同用户其他Provider"""
        async with AsyncSession(async_engine) as session:
            statement = select(LLMProviderTable).where(
                LLMProviderTable.id == provider_id,
                LLMProviderTable.user_id == user_id
            )
            result = await session.execute(statement)
            provider = result.scalars().first()

            if not provider:
                return None

            # 如果要启用，先关闭同用户其他Provider
            if kwargs.get("enable", False):
                await cls._disable_all(session, user_id, exclude_id=provider_id)

            for key, value in kwargs.items():
                if hasattr(provider, key) and value is not None:
                    setattr(provider, key, value)

            session.add(provider)
            await session.commit()
            await session.refresh(provider)
            return provider

    @classmethod
    async def delete(cls, provider_id: int, user_id: int) -> bool:
        """删除Provider"""
        async with AsyncSession(async_engine) as session:
            statement = select(LLMProviderTable).where(
                LLMProviderTable.id == provider_id,
                LLMProviderTable.user_id == user_id
            )
            result = await session.execute(statement)
            provider = result.scalars().first()

            if provider:
                await session.delete(provider)
                await session.commit()
                return True
            return False

    @classmethod
    async def enable_provider(cls, provider_id: int, user_id: int) -> Optional[LLMProviderTable]:
        """启用指定Provider（互斥，自动关闭同用户其他）"""
        async with AsyncSession(async_engine) as session:
            # 先关闭所有
            await cls._disable_all(session, user_id)

            # 再启用指定的
            statement = select(LLMProviderTable).where(
                LLMProviderTable.id == provider_id,
                LLMProviderTable.user_id == user_id
            )
            result = await session.execute(statement)
            provider = result.scalars().first()

            if not provider:
                return None

            provider.enable = True
            session.add(provider)
            await session.commit()
            await session.refresh(provider)
            return provider

    @classmethod
    async def _disable_all(cls, session: AsyncSession, user_id: int, exclude_id: Optional[int] = None):
        """关闭用户所有enable的Provider（内部方法，在session内使用）"""
        statement = select(LLMProviderTable).where(
            LLMProviderTable.user_id == user_id,
            LLMProviderTable.enable == True
        )
        if exclude_id:
            statement = statement.where(LLMProviderTable.id != exclude_id)

        result = await session.execute(statement)
        providers = result.scalars().all()
        for p in providers:
            p.enable = False
            session.add(p)

