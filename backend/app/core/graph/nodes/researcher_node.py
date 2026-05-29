"""Researcher Agent 节点 - 信息检索专家"""
from langgraph.types import StreamWriter

from app.core.graph.state import ChatState
from app.core.agents.react import ResearcherAgent

# scratchpad 中每条 Agent 输出的最大字符数
SCRATCHPAD_MAX_OUTPUT = 1000


async def researcher_node(state: ChatState, writer: StreamWriter) -> dict:
    """Researcher Agent 节点 - 信息检索"""
    response = await ResearcherAgent.stream_run(state, writer)
    return {
        "response": response,
        "agent_scratchpad": [{"agent": ResearcherAgent.name, "output": response[:SCRATCHPAD_MAX_OUTPUT]}],
    }

