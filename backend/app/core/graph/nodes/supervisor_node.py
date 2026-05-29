"""Supervisor 节点 - 意图路由"""
from loguru import logger
from app.core.graph.state import ChatState
from app.core.agents.llm import SupervisorAgent
from app.core.agents.llm.supervisor_agent import SYSTEM_AGENTS


async def supervisor_node(state: ChatState) -> dict:
    """Supervisor 节点 - 意图路由

    编排逻辑：
    1. 从 state 获取用户自建 Agent 描述
    2. 调用 SupervisorAgent 路由（动态注入 Agent 描述）
    3. 验证结果合法性，不合法则尝试模糊匹配
    4. 仍不合法则降级为 chat
    5. 映射到 Graph 状态
    """
    # 获取用户自建 Agent 描述（动态）
    user_agents_desc = state.get("user_agents_desc", [])

    # 构建合法 Agent 名称集合（系统 + 用户自建）
    valid_agents = set(SYSTEM_AGENTS)
    for ua in user_agents_desc:
        agent_name = ua.get("name", "")
        if agent_name:
            valid_agents.add(agent_name)

    # 调用 SupervisorAgent 路由（传入用户 Agent 描述）
    result = await SupervisorAgent.route(state, user_agents_desc=user_agents_desc)

    # Agent 返回 None（调用失败）→ 降级为 chat
    if result is None:
        logger.warning("Supervisor Agent 返回 None，降级为 chat")
        return {"next_agent": "chat"}

    # 验证结果合法性
    next_agent = result
    if next_agent not in valid_agents:
        # 尝试模糊匹配
        for agent_name in valid_agents:
            if agent_name in next_agent:
                next_agent = agent_name
                break
        else:
            logger.warning(f"Supervisor 返回了无效的 Agent 名称: {result}，降级为 chat")
            next_agent = "chat"

    retry_count = state.get("retry_count", 0)
    logger.info(f"Supervisor 路由决策: {next_agent} (重试次数: {retry_count})")
    return {"next_agent": next_agent}

