"""Embedding Provider DAO 层"""
from typing import Optional
from sqlmodel import select
from loguru import logger

from app.database.engine import async_engine
from app.database.models.embedding_provider import EmbeddingProviderTable
from sqlmodel.ext.asyncio.session import AsyncSession


class EmbeddingProviderDao:
    """Embedding Provider 数据访问对象"""

    @classmethod
    async def get_by_user(cls, user_id: int) -> Optional[EmbeddingProviderTable]:
        """获取用户的Embedding Provider（每用户仅一条）"""
        async with AsyncSession(async_engine) as session:
            statement = select(EmbeddingProviderTable).where(
                EmbeddingProviderTable.user_id == user_id
            )
            result = await session.execute(statement)
            return result.scalars().first()

    @classmethod
    async def create(cls, provider: EmbeddingProviderTable) -> EmbeddingProviderTable:
        """创建Embedding Provider（如果已存在则更新）"""
        async with AsyncSession(async_engine) as session:
            # 检查是否已存在
            existing = await session.execute(
                select(EmbeddingProviderTable).where(
                    EmbeddingProviderTable.user_id == provider.user_id
                )
            )
            existing_provider = existing.scalars().first()

            if existing_provider:
                # 更新已有记录
                existing_provider.api_key = provider.api_key
                existing_provider.base_url = provider.base_url
                existing_provider.model = provider.model
                session.add(existing_provider)
                await session.commit()
                await session.refresh(existing_provider)
                return existing_provider
            else:
                # 新建记录
                session.add(provider)
                await session.commit()
                await session.refresh(provider)
                return provider

    @classmethod
    async def update(cls, user_id: int, **kwargs) -> Optional[EmbeddingProviderTable]:
        """更新用户的Embedding Provider"""
        async with AsyncSession(async_engine) as session:
            statement = select(EmbeddingProviderTable).where(
                EmbeddingProviderTable.user_id == user_id
            )
            result = await session.execute(statement)
            provider = result.scalars().first()

            if not provider:
                return None

            for key, value in kwargs.items():
                if hasattr(provider, key) and value is not None:
                    setattr(provider, key, value)

            session.add(provider)
            await session.commit()
            await session.refresh(provider)
            return provider

    @classmethod
    async def delete(cls, user_id: int) -> bool:
        """删除用户的Embedding Provider"""
        async with AsyncSession(async_engine) as session:
            statement = select(EmbeddingProviderTable).where(
                EmbeddingProviderTable.user_id == user_id
            )
            result = await session.execute(statement)
            provider = result.scalars().first()

            if provider:
                await session.delete(provider)
                await session.commit()
                return True
            return False
