"""Reviewer 节点 - 审查回复并决定下一步"""
from loguru import logger
from app.core.graph.state import ChatState
from app.core.agents.llm import ReviewerAgent
from app.services.settings_service import SettingsFactory


async def reviewer_node(state: ChatState) -> dict:
    """Reviewer 节点 - 审查回复并决定下一步

    编排逻辑：
    1. 超过最大重试次数 → 强制通过
    2. 调用 ReviewerAgent 审查
    3. 映射 Agent 结果到 Graph 状态
       - advance: 当前步骤完成，推进到计划下一步
       - pass: 整体任务完成
       - retry: 当前步骤有问题，回到 Supervisor 重新规划
    4. 异常兜底 → 默认通过
    """
    retry_count = state.get("retry_count", 0)
    task_plan = state.get("task_plan", [])
    plan_index = state.get("plan_index", 0)

    # 超过最大重试次数，强制通过
    reviewer_max_retries = SettingsFactory.get(key="REVIEWER_MAX_RETRIES")
    if retry_count >= reviewer_max_retries:
        logger.warning(f"Reviewer: 已达最大重试次数 {retry_count}，强制通过")
        return {"review_result": "pass", "review_feedback": "", "retry_count": retry_count}

    # 调用 Agent 审查
    result = await ReviewerAgent.review(state)

    # Agent 返回 None（解析失败或异常）→ 默认通过
    if result is None:
        logger.warning("Reviewer Agent 返回 None，默认通过")
        return {"review_result": "pass", "review_feedback": "", "retry_count": retry_count}

    # 映射 Agent 结果到 Graph 状态
    review_result = result.get("result", "pass")
    review_feedback = result.get("feedback", "")

    if review_result == "advance":
        # 当前步骤完成，检查是否真的还有下一步
        if task_plan and plan_index + 1 < len(task_plan):
            logger.info(f"Reviewer 推进: 步骤 {plan_index + 1}/{len(task_plan)} 完成，下一步 → {task_plan[plan_index + 1]}")
            return {"review_result": "advance", "review_feedback": "", "retry_count": retry_count}
        else:
            # 计划已全部执行完，直接通过
            logger.info("Reviewer: 计划已全部执行完，通过")
            return {"review_result": "pass", "review_feedback": "", "retry_count": retry_count}

    elif review_result == "retry":
        new_retry_count = retry_count + 1
        logger.info(f"Reviewer 重试: {review_feedback[:100]} (重试次数: {new_retry_count})")
        return {"review_result": "retry", "review_feedback": review_feedback, "retry_count": new_retry_count}

    else:
        # pass
        return {"review_result": "pass", "review_feedback": "", "retry_count": retry_count}

