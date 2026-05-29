
"""用户配置 DAO 层 - 一条 JSON 记录存储用户所有配置"""
import json
from typing import Dict, Optional
from sqlmodel import select
from loguru import logger

from app.database.engine import async_engine
from app.database.models.user_setting import UserSetting
from sqlmodel.ext.asyncio.session import AsyncSession


class UserSettingDao:
    """用户配置数据访问对象 - 每个用户一条 JSON 记录"""

    @classmethod
    async def get_by_user_id(cls, user_id: int) -> Optional[UserSetting]:
        """获取用户配置记录（一条）"""
        async with AsyncSession(async_engine) as session:
            statement = select(UserSetting).where(UserSetting.user_id == user_id)
            result = await session.execute(statement)
            return result.scalars().first()

    @classmethod
    async def get_settings_json(cls, user_id: int) -> Dict:
        """获取用户配置的 JSON 字典，不存在返回空字典"""
        record = await cls.get_by_user_id(user_id)
        if record and record.settings:
            try:
                return json.loads(record.settings)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"用户 {user_id} 的配置 JSON 解析失败，返回空字典")
        return {}

    @classmethod
    async def upsert(cls, user_id: int, settings_json: str) -> UserSetting:
        """插入或更新用户配置（整体 JSON 写入）"""
        from datetime import datetime
        async with AsyncSession(async_engine) as session:
            statement = select(UserSetting).where(UserSetting.user_id == user_id)
            result = await session.execute(statement)
            setting = result.scalars().first()

            if setting:
                setting.settings = settings_json
                setting.updated_at = datetime.now()
                session.add(setting)
            else:
                setting = UserSetting(
                    user_id=user_id,
                    settings=settings_json,
                    updated_at=datetime.now()
                )
                session.add(setting)

            await session.commit()
            await session.refresh(setting)
            return setting

    @classmethod
    async def delete_by_user_id(cls, user_id: int) -> bool:
        """删除用户配置记录"""
        async with AsyncSession(async_engine) as session:
            statement = select(UserSetting).where(UserSetting.user_id == user_id)
            result = await session.execute(statement)
            setting = result.scalars().first()

            if setting:
                await session.delete(setting)
                await session.commit()
                return True
            return False
