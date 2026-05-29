"""Token 使用量统计 DAO 层"""
from typing import List, Optional
from datetime import date, timedelta
from sqlmodel import select, func
from loguru import logger

from app.database.engine import async_engine
from app.database.models.usage_stats import UsageStatsTable
from sqlmodel.ext.asyncio.session import AsyncSession


class UsageStatsDao:
    """Token 使用量统计数据访问对象"""

    @classmethod
    async def upsert_usage_stats(
        cls,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageStatsTable:
        """
        累加 Token 使用记录：同一天 + 同一模型 + 同一用户则累加，否则新建

        Args:
            user_id: 用户ID
            model: 模型名称
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数

        Returns:
            UsageStatsTable: 更新或创建的记录
        """
        today = date.today()

        async with AsyncSession(async_engine) as session:
            statement = select(UsageStatsTable).where(
                UsageStatsTable.user_id == user_id,
                UsageStatsTable.model == model,
                UsageStatsTable.stat_date == today,
            )
            result = await session.execute(statement)
            existing = result.scalar_one_or_none()

            if existing:
                existing.input_tokens += input_tokens
                existing.output_tokens += output_tokens
                existing.request_count += 1
                session.add(existing)
                await session.commit()
                await session.refresh(existing)
                logger.debug(
                    f"Token 累加: user={user_id[:8]}, model={model}, "
                    f"+input={input_tokens}, +output={output_tokens}"
                )
                return existing
            else:
                record = UsageStatsTable(
                    user_id=user_id,
                    model=model,
                    stat_date=today,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    request_count=1,
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)
                logger.debug(
                    f"Token 新建: user={user_id[:8]}, model={model}, "
                    f"input={input_tokens}, output={output_tokens}"
                )
                return record

    @classmethod
    def upsert_usage_stats_sync(
        cls,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageStatsTable:
        """
        累加 Token 使用记录（同步版本，供 Callback 使用）

        同一天 + 同一模型 + 同一用户则累加，否则新建。
        """
        from app.database.engine import engine as sync_engine
        from sqlmodel import Session

        today = date.today()

        with Session(sync_engine) as session:
            statement = select(UsageStatsTable).where(
                UsageStatsTable.user_id == user_id,
                UsageStatsTable.model == model,
                UsageStatsTable.stat_date == today,
            )
            existing = session.exec(statement).first()

            if existing:
                existing.input_tokens += input_tokens
                existing.output_tokens += output_tokens
                existing.request_count += 1
                session.add(existing)
                session.commit()
                session.refresh(existing)
                logger.debug(
                    f"Token 累加(sync): user={user_id[:8]}, model={model}, "
                    f"+input={input_tokens}, +output={output_tokens}"
                )
                return existing
            else:
                record = UsageStatsTable(
                    user_id=user_id,
                    model=model,
                    stat_date=today,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    request_count=1,
                )
                session.add(record)
                session.commit()
                session.refresh(record)
                logger.debug(
                    f"Token 新建(sync): user={user_id[:8]}, model={model}, "
                    f"input={input_tokens}, output={output_tokens}"
                )
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
        start_date = date.today() - timedelta(days=delta_days)

        async with AsyncSession(async_engine) as session:
            statement = (
                select(UsageStatsTable)
                .where(
                    UsageStatsTable.user_id == user_id,
                    UsageStatsTable.stat_date >= start_date,
                )
                .order_by(UsageStatsTable.stat_date.asc())
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
        按日期 + 模型查询 Token 使用量

        由于数据已经按天聚合存储，直接查询即可，无需再 GROUP BY。

        Returns:
            List[dict]: [{"date": "2025-01-15", "model": "gpt-4",
                          "input_tokens": 100, "output_tokens": 200, "total_tokens": 300}]
        """
        start_date = date.today() - timedelta(days=delta_days)

        async with AsyncSession(async_engine) as session:
            statement = (
                select(UsageStatsTable)
                .where(
                    UsageStatsTable.user_id == user_id,
                    UsageStatsTable.stat_date >= start_date,
                )
                .order_by(UsageStatsTable.stat_date, UsageStatsTable.model)
            )
            if model:
                statement = statement.where(UsageStatsTable.model == model)

            result = await session.execute(statement)
            rows = result.scalars().all()

            return [
                {
                    "date": str(row.stat_date),
                    "model": row.model,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.input_tokens + row.output_tokens,
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
        按日期 + 模型查询调用次数

        由于数据已经按天聚合存储，直接查询 request_count 即可。

        Returns:
            List[dict]: [{"date": "2025-01-15", "model": "gpt-4", "count": 10}]
        """
        start_date = date.today() - timedelta(days=delta_days)

        async with AsyncSession(async_engine) as session:
            statement = (
                select(UsageStatsTable)
                .where(
                    UsageStatsTable.user_id == user_id,
                    UsageStatsTable.stat_date >= start_date,
                )
                .order_by(UsageStatsTable.stat_date, UsageStatsTable.model)
            )
            if model:
                statement = statement.where(UsageStatsTable.model == model)

            result = await session.execute(statement)
            rows = result.scalars().all()

            return [
                {
                    "date": str(row.stat_date),
                    "model": row.model,
                    "count": row.request_count,
                }
                for row in rows
            ]
