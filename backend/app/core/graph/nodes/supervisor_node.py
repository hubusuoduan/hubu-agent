"""Supervisor 节点 - 任务规划与调度"""
from loguru import logger
from app.core.graph.state import ChatState
from app.core.agents.llm import SupervisorAgent
from app.core.agents.llm.supervisor_agent import SYSTEM_AGENTS


def _validate_and_fix_plan(plan: list, valid_agents: set) -> list:
    """验证并修正任务计划中的 Agent 名称

    Args:
        plan: 原始计划列表，格式: [{"agent": "xxx", "task": "xxx"}, ...]
        valid_agents: 合法 Agent 名称集合

    Returns:
        修正后的计划列表
    """
    fixed = []
    for step in plan:
        agent_name = step.get("agent", "") if isinstance(step, dict) else str(step)
        task_desc = step.get("task", "") if isinstance(step, dict) else ""

        if agent_name in valid_agents:
            fixed.append({"agent": agent_name, "task": task_desc})
        else:
            # 尝试模糊匹配
            matched = None
            for valid_name in valid_agents:
                if valid_name in agent_name or agent_name in valid_name:
                    matched = valid_name
                    break
            if matched:
                fixed.append({"agent": matched, "task": task_desc})
                logger.info(f"Supervisor 模糊匹配: {agent_name} → {matched}")
            else:
                logger.warning(f"Supervisor 计划中无效 Agent: {agent_name}，跳过")
    return fixed


async def supervisor_node(state: ChatState) -> dict:
    """Supervisor 节点 - 任务规划与调度

    编排逻辑：
    1. 检查是否已有任务计划且未执行完 → 直接推进到下一步
    2. 否则调用 SupervisorAgent 制定新计划
    3. 验证计划合法性
    4. 设置 next_agent 和 task_instruction
    """
    # 获取用户自建 Agent 描述（动态）
    user_agents_desc = state.get("user_agents_desc", [])

    # 构建合法 Agent 名称集合（系统 + 用户自建）
    valid_agents = set(SYSTEM_AGENTS)
    for ua in user_agents_desc:
        agent_name = ua.get("name", "")
        if agent_name:
            valid_agents.add(agent_name)

    task_plan = state.get("task_plan", [])
    plan_index = state.get("plan_index", 0)
    review_result = state.get("review_result", "")

    # 情况1：已有计划且 Reviewer 说推进到下一步 → 直接推进
    if task_plan and review_result == "advance":
        plan_index += 1
        if plan_index < len(task_plan):
            step = task_plan[plan_index]
            next_agent = step.get("agent", "chat") if isinstance(step, dict) else str(step)
            task_instruction = step.get("task", "") if isinstance(step, dict) else ""
            logger.info(f"Supervisor 推进计划: 步骤 {plan_index + 1}/{len(task_plan)} → {next_agent}")
            return {
                "next_agent": next_agent,
                "plan_index": plan_index,
                "task_instruction": task_instruction,
                "review_result": "",
                "review_feedback": "",
            }
        else:
            # 计划已全部执行完，不应该走到这里（Reviewer 应该给 pass）
            logger.info("Supervisor 计划已全部执行完，结束")
            return {"next_agent": "chat", "plan_index": plan_index, "task_instruction": "", "review_result": "", "review_feedback": ""}

    # 情况2：需要重新规划（首次 / Reviewer 打回 / 计划执行完但未通过）
    result = await SupervisorAgent.plan(state, user_agents_desc=user_agents_desc)

    # Agent 返回 None（调用失败）→ 降级为 chat
    if result is None:
        logger.warning("Supervisor Agent 返回 None，降级为 chat")
        return {"next_agent": "chat", "task_plan": [{"agent": "chat", "task": ""}], "plan_index": 0, "task_instruction": ""}

    # 验证并修正计划
    plan = _validate_and_fix_plan(result, valid_agents)
    if not plan:
        logger.warning("Supervisor 计划验证后为空，降级为 chat")
        return {"next_agent": "chat", "task_plan": [{"agent": "chat", "task": ""}], "plan_index": 0, "task_instruction": ""}

    retry_count = state.get("retry_count", 0)
    first_step = plan[0]
    next_agent = first_step.get("agent", "chat")
    task_instruction = first_step.get("task", "")
    logger.info(f"Supervisor 新计划: {plan}，首步 → {next_agent} (重试次数: {retry_count})")

    return {
        "next_agent": next_agent,
        "task_plan": plan,
        "plan_index": 0,
        "task_instruction": task_instruction,
        "review_result": "",
        "review_feedback": "",
    }

