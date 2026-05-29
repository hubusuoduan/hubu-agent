"""Coder Agent 节点 - 代码执行专家"""
from langgraph.types import StreamWriter

from app.core.graph.state import ChatState
from app.core.agents.react import CoderAgent

# scratchpad 中每条 Agent 输出的最大字符数
SCRATCHPAD_MAX_OUTPUT = 1000


async def coder_node(state: ChatState, writer: StreamWriter) -> dict:
    """Coder Agent 节点 - 代码执行"""
    response = await CoderAgent.stream_run(state, writer)
    return {
        "response": response,
        "agent_scratchpad": [{"agent": CoderAgent.name, "output": response[:SCRATCHPAD_MAX_OUTPUT]}],
    }

