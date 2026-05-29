"""数据库会话管理"""
from contextlib import asynccontextmanager
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
        # 区分HTTPException(如认证异常)和数据库异常
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            # 认证/权限等HTTP异常，不需要回滚数据库，直接抛出
            logger.warning(f'请求异常({e.status_code}): {e.detail}')
            raise
        logger.error(f'数据库会话异常: {e}')
        await session.rollback()
        raise
    finally:
        await session.close()
        logger.debug('数据库会话已关闭')


@asynccontextmanager
async def get_session_ctx() -> AsyncGenerator[AsyncSession, None]:
    """异步数据库会话上下文管理器（非依赖注入场景使用）

    用法:
        async with get_session_ctx() as session:
            result = await session.execute(...)

    替代 async for session in get_async_session() + break 的不优雅写法。
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
        