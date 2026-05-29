"""用户自建 Agent DAO 层"""
from typing import List, Optional
from sqlmodel import select
from loguru import logger

from app.database.engine import async_engine
from app.database.models.user_agent import UserAgentTable
from sqlmodel.ext.asyncio.session import AsyncSession


class UserAgentDao:
    """用户自建 Agent 数据访问对象"""

    @classmethod
    async def create_agent(
        cls,
        user_id: int,
        name: str,
        display_name: str,
        description: str,
        agent_path: str,
        enabled: int = 1,
    ) -> UserAgentTable:
        """创建用户自建 Agent 记录"""
        agent = UserAgentTable(
            user_id=user_id,
            name=name,
            display_name=display_name,
            description=description,
            agent_path=agent_path,
            enabled=enabled,
        )
        async with AsyncSession(async_engine) as session:
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            logger.info(f"创建用户 Agent 成功: {name}, user_id: {user_id}")
            return agent

    @classmethod
    async def get_by_id(cls, agent_id: int) -> Optional[UserAgentTable]:
        """根据 ID 获取 Agent"""
        async with AsyncSession(async_engine) as session:
            statement = select(UserAgentTable).where(UserAgentTable.id == agent_id)
            result = await session.execute(statement)
            return result.scalars().first()

    @classmethod
    async def get_by_user_and_name(cls, user_id: int, name: str) -> Optional[UserAgentTable]:
        """根据用户ID和Agent名称获取 Agent（用于名称唯一性校验）"""
        async with AsyncSession(async_engine) as session:
            statement = select(UserAgentTable).where(
                UserAgentTable.user_id == user_id,
                UserAgentTable.name == name,
            )
            result = await session.execute(statement)
            return result.scalars().first()

    @classmethod
    async def get_enabled_by_user_id(cls, user_id: int) -> List[UserAgentTable]:
        """获取用户所有启用的 Agent（Supervisor 路由用）"""
        async with AsyncSession(async_engine) as session:
            statement = (
                select(UserAgentTable)
                .where(UserAgentTable.user_id == user_id, UserAgentTable.enabled == 1)
                .order_by(UserAgentTable.create_time.desc())
            )
            result = await session.execute(statement)
            agents = result.scalars().all()
            logger.info(f"获取用户启用的 Agent: user_id={user_id}, 数量: {len(agents)}")
            return agents

    @classmethod
    async def get_all_by_user_id(cls, user_id: int) -> List[UserAgentTable]:
        """获取用户所有 Agent（含禁用的，管理页面用）"""
        async with AsyncSession(async_engine) as session:
            statement = (
                select(UserAgentTable)
                .where(UserAgentTable.user_id == user_id)
                .order_by(UserAgentTable.create_time.desc())
            )
            result = await session.execute(statement)
            return result.scalars().all()

    @classmethod
    async def update_agent(cls, agent_id: int, **kwargs) -> Optional[UserAgentTable]:
        """更新 Agent 信息"""
        async with AsyncSession(async_engine) as session:
            statement = select(UserAgentTable).where(UserAgentTable.id == agent_id)
            result = await session.execute(statement)
            agent = result.scalars().first()

            if agent:
                for key, value in kwargs.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
                session.add(agent)
                await session.commit()
                await session.refresh(agent)
                logger.info(f"更新用户 Agent: {agent_id}, 字段: {list(kwargs.keys())}")
                return agent
            return None

    @classmethod
    async def delete_agent(cls, agent_id: int) -> bool:
        """删除 Agent 记录"""
        async with AsyncSession(async_engine) as session:
            statement = select(UserAgentTable).where(UserAgentTable.id == agent_id)
            result = await session.execute(statement)
            agent = result.scalars().first()

            if agent:
                await session.delete(agent)
                await session.commit()
                logger.info(f"删除用户 Agent: {agent_id}")
                return True
            return False

    @classmethod
    async def toggle_enabled(cls, agent_id: int, enabled: int) -> Optional[UserAgentTable]:
        """切换 Agent 启用/禁用状态"""
        return await cls.update_agent(agent_id, enabled=enabled)
