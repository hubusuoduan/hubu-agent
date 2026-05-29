"""Skill Agent 节点 - 技能执行专家"""
from langgraph.types import StreamWriter

from app.core.graph.state import ChatState
from app.core.agents.react import SkillAgent

# scratchpad 中每条 Agent 输出的最大字符数
SCRATCHPAD_MAX_OUTPUT = 1000


async def skill_node(state: ChatState, writer: StreamWriter) -> dict:
    """Skill Agent 节点 - 技能执行"""
    response = await SkillAgent.stream_run(state, writer)
    return {
        "response": response,
        "agent_scratchpad": [{"agent": SkillAgent.name, "output": response[:SCRATCHPAD_MAX_OUTPUT]}],
    }

