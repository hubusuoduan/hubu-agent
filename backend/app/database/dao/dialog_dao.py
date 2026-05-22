"""对话DAO层"""
from typing import List, Optional
from sqlmodel import select
from loguru import logger

from app.database.engine import async_engine
from app.database.models.dialog import DialogTable
from sqlmodel.ext.asyncio.session import AsyncSession


class DialogDao:
    """对话数据访问对象"""

    @classmethod
    async def create_dialog(
        cls,
        name: str = "新对话",
        user_id: Optional[int] = None
    ) -> DialogTable:
        """
        创建新对话

        Args:
            name: 对话名称
            user_id: 用户ID（关联users表）

        Returns:
            DialogTable: 创建的对话记录
        """
        dialog = DialogTable(name=name, user_id=user_id)

        async with AsyncSession(async_engine) as session:
            session.add(dialog)
            await session.commit()
            await session.refresh(dialog)
            logger.info(f"创建对话成功: {dialog.dialog_id}, user_id: {user_id}")
            return dialog

    @classmethod
    async def get_dialog_by_id(cls, dialog_id: str) -> Optional[DialogTable]:
        """
        根据ID获取对话

        Args:
            dialog_id: 对话ID

        Returns:
            Optional[DialogTable]: 对话记录
        """
        async with AsyncSession(async_engine) as session:
            statement = select(DialogTable).where(
                DialogTable.dialog_id == dialog_id
            )
            result = await session.execute(statement)
            dialog = result.scalars().first()
            logger.info(f"获取对话: {dialog_id}")
            return dialog

    @classmethod
    async def get_dialogs_by_user_id(
        cls,
        user_id: int,
        limit: int = 50
    ) -> List[DialogTable]:
        """
        获取用户的对话列表

        Args:
            user_id: 用户ID
            limit: 限制返回数量

        Returns:
            List[DialogTable]: 对话列表
        """
        async with AsyncSession(async_engine) as session:
            statement = (
                select(DialogTable)
                .where(DialogTable.user_id == user_id)
                .order_by(DialogTable.update_time.desc())
                .limit(limit)
            )
            result = await session.execute(statement)
            dialogs = result.scalars().all()
            logger.info(f"获取用户对话列表: user_id={user_id}, 数量: {len(dialogs)}")
            return dialogs

    @classmethod
    async def update_dialog_name(cls, dialog_id: str, name: str) -> Optional[DialogTable]:
        """
        更新对话名称

        Args:
            dialog_id: 对话ID
            name: 新名称

        Returns:
            Optional[DialogTable]: 更新后的对话记录
        """
        async with AsyncSession(async_engine) as session:
            statement = select(DialogTable).where(
                DialogTable.dialog_id == dialog_id
            )
            result = await session.execute(statement)
            dialog = result.scalars().first()

            if dialog:
                dialog.name = name
                session.add(dialog)
                await session.commit()
                await session.refresh(dialog)
                logger.info(f"更新对话名称: {dialog_id} -> {name}")
                return dialog
            return None

    @classmethod
    async def update_dialog_summary(cls, dialog_id: str, summary: str) -> Optional[DialogTable]:
        """
        更新对话摘要

        Args:
            dialog_id: 对话ID
            summary: 对话摘要

        Returns:
            Optional[DialogTable]: 更新后的对话记录
        """
        async with AsyncSession(async_engine) as session:
            statement = select(DialogTable).where(
                DialogTable.dialog_id == dialog_id
            )
            result = await session.execute(statement)
            dialog = result.scalars().first()

            if dialog:
                dialog.summary = summary
                session.add(dialog)
                await session.commit()
                await session.refresh(dialog)
                logger.info(f"更新对话摘要: {dialog_id}")
                return dialog
            return None

    @classmethod
    async def delete_dialog(cls, dialog_id: str) -> bool:
        """
        删除对话（同时删除关联的历史记录）

        Args:
            dialog_id: 对话ID

        Returns:
            bool: 是否删除成功
        """
        async with AsyncSession(async_engine) as session:
            statement = select(DialogTable).where(
                DialogTable.dialog_id == dialog_id
            )
            result = await session.execute(statement)
            dialog = result.scalars().first()

            if dialog:
                # 先删除关联的历史记录
                from app.database.models.history import HistoryTable
                history_statement = select(HistoryTable).where(
                    HistoryTable.dialog_id == dialog_id
                )
                history_result = await session.execute(history_statement)
                histories = history_result.scalars().all()
                for history in histories:
                    await session.delete(history)

                await session.delete(dialog)
                await session.commit()
                logger.info(f"删除对话及历史记录成功: {dialog_id}, 历史记录数: {len(histories)}")
                return True

            return False
