"""数据库会话管理"""
from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.database.engine import async_engine


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    异步数据库会话依赖
    
    Yields:
        AsyncSession: 异步数据库会话实例
    """
    if async_engine is None:
        raise RuntimeError("数据库引擎未初始化")
    
    session = AsyncSession(async_engine)
    
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f'数据库会话异常: {e}')
        await session.rollback()
        raise
    finally:
        await session.close()
        logger.debug('数据库会话已关闭')
        