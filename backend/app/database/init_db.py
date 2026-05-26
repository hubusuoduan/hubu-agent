"""数据库初始化脚本"""
import asyncio
from sqlmodel import SQLModel
from loguru import logger

from app.database.engine import engine, async_engine
from app.database.models import DialogTable, HistoryTable, KnowledgeTable, KnowledgeFileTable, User, UsageStatsTable
from sqlalchemy import inspect, text


def _migrate_dialog_table(engine):
    """增量迁移：为 dialog 表添加 is_pinned、is_starred、pinned_at 列（如果不存在）"""
    insp = inspect(engine)
    if "dialog" not in insp.get_table_names():
        return
    existing_columns = {col["name"] for col in insp.get_columns("dialog")}
    with engine.connect() as conn:
        if "is_pinned" not in existing_columns:
            conn.execute(text("ALTER TABLE dialog ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
            logger.info("迁移: dialog 表添加 is_pinned 列")
        if "is_starred" not in existing_columns:
            conn.execute(text("ALTER TABLE dialog ADD COLUMN is_starred INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
            logger.info("迁移: dialog 表添加 is_starred 列")
        if "pinned_at" not in existing_columns:
            conn.execute(text("ALTER TABLE dialog ADD COLUMN pinned_at DATETIME NULL"))
            conn.commit()
            logger.info("迁移: dialog 表添加 pinned_at 列")


async def init_db():
    """
    初始化数据库表

    创建所有定义的表结构
    """
    try:
        # 使用同步引擎创建表
        if engine:
            logger.info("开始创建数据库表...")
            SQLModel.metadata.create_all(engine)
            logger.info("数据库表创建成功")

            # 增量迁移：为已有表添加新列
            _migrate_dialog_table(engine)

            # 列出创建的表
            tables = SQLModel.metadata.tables.keys()
            logger.info(f"已创建的表: {', '.join(tables)}")
        else:
            logger.error("数据库引擎未初始化，无法创建表")

    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise


async def drop_db():
    """
    删除所有数据库表（谨慎使用）
    """
    try:
        if engine:
            logger.warning("开始删除数据库表...")
            SQLModel.metadata.drop_all(engine)
            logger.warning("数据库表已删除")
        else:
            logger.error("数据库引擎未初始化")

    except Exception as e:
        logger.error(f"数据库表删除失败: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(init_db())
