"""数据库引擎配置"""
from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from loguru import logger

from app.config import settings


def get_database_url() -> str:
    """
    构建数据库连接URL
    
    Returns:
        数据库连接字符串
    """
    return (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        f"?charset=utf8mb4"
    )


def get_async_database_url() -> str:
    """
    构建异步数据库连接URL
    
    Returns:
        异步数据库连接字符串
    """
    return (
        f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        f"?charset=utf8mb4"
    )


# 创建同步引擎（用于数据库初始化）
try:
    engine = create_engine(
        get_database_url(),
        echo=settings.DEBUG,  # 开发环境显示SQL语句
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )
    logger.info("同步数据库引擎创建成功")
except Exception as e:
    logger.warning(f"同步数据库引擎创建失败: {e}")
    engine = None


# 创建异步引擎（用于应用运行）
try:
    async_engine = create_async_engine(
        get_async_database_url(),
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600
    )
    logger.info("异步数据库引擎创建成功")
except Exception as e:
    logger.warning(f"异步数据库引擎创建失败: {e}")
    async_engine = None
