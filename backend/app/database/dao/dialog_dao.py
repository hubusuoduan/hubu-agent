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
        user_id: str = "default_user"
    ) -> DialogTable:
        """
        创建新对话
        
        Args:
            name: 对话名称
            user_id: 用户ID
            
        Returns:
            DialogTable: 创建的对话记录
        """
        dialog = DialogTable(name=name, user_id=user_id)
        
        async with AsyncSession(async_engine) as session:
            session.add(dialog)
            await session.commit()
            await session.refresh(dialog)
            logger.info(f"创建对话成功: {dialog.dialog_id}")
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
        user_id: str, 
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
                .order_by(DialogTable.create_time.desc())
                .limit(limit)
            )
            result = await session.execute(statement)
            dialogs = result.scalars().all()
            logger.info(f"获取用户对话列表: {user_id}, 数量: {len(dialogs)}")
            return dialogs

    @classmethod
    async def delete_dialog(cls, dialog_id: str) -> bool:
        """
        删除对话
        
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
                await session.delete(dialog)
                await session.commit()
                logger.info(f"删除对话成功: {dialog_id}")
                return True
            
            return False
