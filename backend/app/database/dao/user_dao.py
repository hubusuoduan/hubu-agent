"""用户数据访问层"""
from typing import Optional, List
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from loguru import logger

from app.database.models.user import User


class UserDAO:
    """用户数据访问对象"""
    
    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            session: 数据库会话
            username: 用户名
            
        Returns:
            用户对象或None
        """
        statement = select(User).where(User.username == username)
        result = await session.exec(statement)
        return result.first()
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            session: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        statement = select(User).where(User.id == user_id)
        result = await session.exec(statement)
        return result.first()
    
    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            session: 数据库会话
            email: 邮箱地址
            
        Returns:
            用户对象或None
        """
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()
    
    @staticmethod
    async def create_user(session: AsyncSession, user: User) -> User:
        """
        创建用户
        
        Args:
            session: 数据库会话
            user: 用户对象
            
        Returns:
            创建后的用户对象
        """
        session.add(user)
        await session.flush()
        await session.refresh(user)
        logger.info(f"用户创建成功: {user.username}")
        return user
    
    @staticmethod
    async def update_user(session: AsyncSession, user: User) -> User:
        """
        更新用户信息
        
        Args:
            session: 数据库会话
            user: 用户对象
            
        Returns:
            更新后的用户对象
        """
        user.updated_at = datetime.now()
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user
