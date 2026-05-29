"""Chat Agent 节点 - 通用对话"""
from langgraph.types import StreamWriter

from app.core.graph.state import ChatState
from app.core.agents.react import ChatAgent

# scratchpad 中每条 Agent 输出的最大字符数
SCRATCHPAD_MAX_OUTPUT = 1000


async def chat_agent_node(state: ChatState, writer: StreamWriter) -> dict:
    """Chat Agent 节点 - 通用对话"""
    response = await ChatAgent.stream_run(state, writer)
    return {
        "response": response,
        "agent_scratchpad": [{"agent": ChatAgent.name, "output": response[:SCRATCHPAD_MAX_OUTPUT]}],
    }


# 保留旧名称的兼容别名
stream_chat_agent_node = chat_agent_node

