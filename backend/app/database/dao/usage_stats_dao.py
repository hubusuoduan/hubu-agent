"""Token 使用量统计 DAO 层"""
from typing import List, Optional
from sqlmodel import select, func
from sqlalchemy import text
from loguru import logger

from app.database.engine import async_engine
from app.database.models.usage_stats import UsageStatsTable
from sqlmodel.ext.asyncio.session import AsyncSession


class UsageStatsDao:
    """Token 使用量统计数据访问对象"""

    @classmethod
    async def create_usage_stats(
        cls,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageStatsTable:
        """
        创建一条 Token 使用记录

        Args:
            user_id: 用户ID
            model: 模型名称
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数

        Returns:
            UsageStatsTable: 创建的记录
        """
        record = UsageStatsTable(
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        async with AsyncSession(async_engine) as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @classmethod
    async def get_usage_by_time_range(
        cls,
        user_id: str,
        delta_days: int = 7,
        model: Optional[str] = None,
    ) -> List[UsageStatsTable]:
        """
        按时间范围查询 Token 使用记录

        Args:
            user_id: 用户ID
            delta_days: 查询最近多少天的数据
            model: 模型名称过滤（可选）

        Returns:
            List[UsageStatsTable]: 使用记录列表
        """
        from datetime import datetime, timedelta

        start_time = datetime.now() - timedelta(days=delta_days)

        async with AsyncSession(async_engine) as session:
            statement = (
                select(UsageStatsTable)
                .where(
                    UsageStatsTable.user_id == user_id,
                    UsageStatsTable.create_time >= start_time,
                )
                .order_by(UsageStatsTable.create_time.asc())
            )
            if model:
                statement = statement.where(UsageStatsTable.model == model)

            result = await session.execute(statement)
            records = result.scalars().all()
            return records

    @classmethod
    async def get_models_by_user(cls, user_id: str) -> List[str]:
        """获取用户使用过的模型列表（去重）"""
        async with AsyncSession(async_engine) as session:
            statement = (
                select(UsageStatsTable.model)
                .where(UsageStatsTable.user_id == user_id)
                .distinct()
                .order_by(UsageStatsTable.model)
            )
            result = await session.execute(statement)
            return [row[0] for row in result.all()]

    @classmethod
    async def get_usage_aggregated(
        cls,
        user_id: str,
        delta_days: int = 7,
        model: Optional[str] = None,
    ) -> List[dict]:
        """
        按日期 + 模型聚合查询 Token 使用量

        在数据库层面完成聚合，避免 Python 层循环。

        Returns:
            List[dict]: [{"date": "2025-01-15", "model": "gpt-4", 
                          "input_tokens": 100, "output_tokens": 200, "total_tokens": 300}]
        """
        from datetime import datetime, timedelta

        start_time = datetime.now() - timedelta(days=delta_days)

        async with AsyncSession(async_engine) as session:
            # 按日期 + 模型聚合
            statement = (
                select(
                    func.date(UsageStatsTable.create_time).label("date"),
                    UsageStatsTable.model,
                    func.sum(UsageStatsTable.input_tokens).label("input_tokens"),
                    func.sum(UsageStatsTable.output_tokens).label("output_tokens"),
                )
                .where(
                    UsageStatsTable.user_id == user_id,
                    UsageStatsTable.create_time >= start_time,
                )
                .group_by(
                    func.date(UsageStatsTable.create_time),
                    UsageStatsTable.model,
                )
                .order_by(text("date"), UsageStatsTable.model)
            )
            if model:
                statement = statement.where(UsageStatsTable.model == model)

            result = await session.execute(statement)
            rows = result.all()

            return [
                {
                    "date": str(row.date),
                    "model": row.model,
                    "input_tokens": int(row.input_tokens or 0),
                    "output_tokens": int(row.output_tokens or 0),
                    "total_tokens": int((row.input_tokens or 0) + (row.output_tokens or 0)),
                }
                for row in rows
            ]

    @classmethod
    async def get_usage_count_aggregated(
        cls,
        user_id: str,
        delta_days: int = 7,
        model: Optional[str] = None,
    ) -> List[dict]:
        """
        按日期 + 模型聚合查询调用次数

        Returns:
            List[dict]: [{"date": "2025-01-15", "model": "gpt-4", "count": 10}]
        """
        from datetime import datetime, timedelta

        start_time = datetime.now() - timedelta(days=delta_days)

        async with AsyncSession(async_engine) as session:
            statement = (
                select(
                    func.date(UsageStatsTable.create_time).label("date"),
                    UsageStatsTable.model,
                    func.count().label("count"),
                )
                .where(
                    UsageStatsTable.user_id == user_id,
                    UsageStatsTable.create_time >= start_time,
                )
                .group_by(
                    func.date(UsageStatsTable.create_time),
                    UsageStatsTable.model,
                )
                .order_by(text("date"), UsageStatsTable.model)
            )
            if model:
                statement = statement.where(UsageStatsTable.model == model)

            result = await session.execute(statement)
            rows = result.all()

            return [
                {
                    "date": str(row.date),
                    "model": row.model,
                    "count": int(row.count),
                }
                for row in rows
            ]
