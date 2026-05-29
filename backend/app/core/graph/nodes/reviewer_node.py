"""Reviewer 节点 - 审查回复质量"""
from loguru import logger
from app.core.graph.state import ChatState
from app.core.agents.llm import ReviewerAgent
from app.services.settings_service import SettingsFactory


async def reviewer_node(state: ChatState) -> dict:
    """Reviewer 节点 - 审查回复质量

    编排逻辑：
    1. 超过最大重试次数 → 强制通过
    2. 调用 ReviewerAgent 审查
    3. 映射 Agent 结果到 Graph 状态
    4. 异常兜底 → 默认通过
    """
    retry_count = state.get("retry_count", 0)

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
    new_retry_count = retry_count + 1 if review_result == "retry" else retry_count

    return {
        "review_result": review_result,
        "review_feedback": review_feedback if review_result == "retry" else "",
        "retry_count": new_retry_count,
    }

