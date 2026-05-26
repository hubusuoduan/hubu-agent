"""Token 使用量统计 API"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.database.dao.usage_stats_dao import UsageStatsDao

router = APIRouter()


class UsageQuery(BaseModel):
    """Token 使用量查询参数"""
    delta_days: int = 7  # 查询最近多少天
    model: Optional[str] = None  # 模型名称过滤


@router.post("/usage", summary="获取 Token 使用量（按日期+模型聚合）")
async def get_usage(
    query: UsageQuery,
    current_user: User = Depends(get_current_user),
):
    """
    获取 Token 使用量，按日期和模型聚合

    返回格式：
    ```json
    {
      "data": [
        {"date": "2025-01-15", "model": "gpt-4", "input_tokens": 100, "output_tokens": 200, "total_tokens": 300}
      ],
      "summary": {
        "total_input_tokens": 1000,
        "total_output_tokens": 2000,
        "total_tokens": 3000
      }
    }
    ```
    """
    try:
        user_id = str(current_user.id)
        delta_days = query.delta_days
        model = query.model

        records = await UsageStatsDao.get_usage_aggregated(
            user_id=user_id,
            delta_days=delta_days,
            model=model,
        )

        # 计算汇总
        total_input = sum(r["input_tokens"] for r in records)
        total_output = sum(r["output_tokens"] for r in records)

        return {
            "data": records,
            "summary": {
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output,
            },
        }
    except Exception as e:
        logger.error(f"获取 Token 使用量失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取 Token 使用量失败: {str(e)}")


@router.post("/usage_count", summary="获取调用次数（按日期+模型聚合）")
async def get_usage_count(
    query: UsageQuery,
    current_user: User = Depends(get_current_user),
):
    """
    获取调用次数，按日期和模型聚合

    返回格式：
    ```json
    {
      "data": [
        {"date": "2025-01-15", "model": "gpt-4", "count": 10}
      ],
      "summary": {
        "total_count": 50
      }
    }
    ```
    """
    try:
        user_id = str(current_user.id)
        delta_days = query.delta_days
        model = query.model

        records = await UsageStatsDao.get_usage_count_aggregated(
            user_id=user_id,
            delta_days=delta_days,
            model=model,
        )

        total_count = sum(r["count"] for r in records)

        return {
            "data": records,
            "summary": {
                "total_count": total_count,
            },
        }
    except Exception as e:
        logger.error(f"获取调用次数失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取调用次数失败: {str(e)}")


@router.get("/models_list", summary="获取用户使用过的模型列表")
async def get_models_list(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户使用过的所有模型（去重）"""
    try:
        user_id = str(current_user.id)
        models = await UsageStatsDao.get_models_by_user(user_id=user_id)
        return {"models": models}
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")
