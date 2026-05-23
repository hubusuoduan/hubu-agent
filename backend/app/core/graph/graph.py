"""Graph 主文件 - 支持多 Agent 组合"""
from typing import Dict, Any, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from loguru import logger

from app.core.graph.state import ChatState
from app.core.graph.nodes.chat_agent_node import chat_agent_node, stream_chat_agent_node
from app.core.graph.nodes.rag_node import rag_node
from app.core.graph.nodes.history_node import history_manager_node
from app.core.graph.nodes.memory_node import memory_node
from app.core.graph.nodes.memory_extract_node import memory_extract_node


def create_chat_graph() -> StateGraph:
    """
    创建聊天 Graph

    Returns:
        编译后的 StateGraph 实例
    """
    # 创建 StateGraph
    workflow = StateGraph(ChatState)

    # 添加节点
    workflow.add_node("rag", rag_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("history_manager", history_manager_node)
    workflow.add_node("chat_agent", chat_agent_node)
    workflow.add_node("memory_extract", memory_extract_node)

    # 设置执行流程：START -> rag -> memory -> history_manager -> chat_agent -> memory_extract -> END
    workflow.add_edge(START, "rag")
    workflow.add_edge("rag", "memory")
    workflow.add_edge("memory", "history_manager")
    workflow.add_edge("history_manager", "chat_agent")
    workflow.add_edge("chat_agent", "memory_extract")
    workflow.add_edge("memory_extract", END)

    # 编译 Graph
    graph = workflow.compile()

    logger.info("Chat Graph 创建成功（包含 RAG 节点、长期记忆节点和历史管理节点）")
    return graph


def create_stream_chat_graph() -> StateGraph:
    """
    创建流式聊天 Graph

    Returns:
        编译后的 StateGraph 实例
    """
    # 创建 StateGraph
    workflow = StateGraph(ChatState)

    # 添加节点
    workflow.add_node("rag", rag_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("history_manager", history_manager_node)
    workflow.add_node("stream_chat_agent", stream_chat_agent_node)
    workflow.add_node("memory_extract", memory_extract_node)

    # 设置执行流程：START -> rag -> memory -> history_manager -> stream_chat_agent -> memory_extract -> END
    workflow.add_edge(START, "rag")
    workflow.add_edge("rag", "memory")
    workflow.add_edge("memory", "history_manager")
    workflow.add_edge("history_manager", "stream_chat_agent")
    workflow.add_edge("stream_chat_agent", "memory_extract")
    workflow.add_edge("memory_extract", END)

    # 编译 Graph
    graph = workflow.compile()

    logger.info("流式 Chat Graph 创建成功（包含 RAG 节点、长期记忆节点和历史管理节点）")
    return graph


# 创建全局 Graph 实例（可按需改为按 session 管理）
chat_graph = create_chat_graph()
stream_chat_graph = create_stream_chat_graph()


async def run_chat_graph(
    user_input: str,
    session_id: str = "default",
    user_id: str = "",
    messages: list = None
) -> Dict[str, Any]:
    """
    运行聊天 Graph

    Args:
        user_input: 用户输入
        session_id: 会话ID
        user_id: 用户ID（用于长期记忆）
        messages: 历史消息列表（可选）

    Returns:
        Graph 执行结果，包含 response
    """
    try:
        # 构建初始状态
        initial_state = {
            "messages": messages or [],
            "user_input": user_input,
            "context": None,
            "session_id": session_id,
            "user_id": user_id,
            "response": ""
        }

        # 执行 Graph
        result = await chat_graph.ainvoke(initial_state)

        logger.info(f"Chat Graph 执行成功，session_id: {session_id}")
        return result

    except Exception as e:
        logger.error(f"Chat Graph 执行失败: {e}")
        raise


async def run_stream_chat_graph(
    user_input: str,
    session_id: str = "default",
    user_id: str = "",
    messages: list = None
) -> AsyncGenerator[str, None]:
    """
    流式运行聊天 Graph

    Args:
        user_input: 用户输入
        session_id: 会话ID
        user_id: 用户ID（用于长期记忆）
        messages: 历史消息列表（可选）

    Yields:
        流式输出的文本片段
    """
    try:
        # 构建初始状态
        initial_state = {
            "messages": messages or [],
            "user_input": user_input,
            "context": None,
            "session_id": session_id,
            "user_id": user_id,
            "response": ""
        }

        # 流式执行 Graph,使用 custom 模式获取事件数据
        async for chunk in stream_chat_graph.astream(initial_state, stream_mode="custom"):
            if isinstance(chunk, dict):
                yield chunk
            elif isinstance(chunk, str) and chunk:
                # 兼容旧格式
                yield {"type": "content", "content": chunk}

        logger.info(f"流式 Chat Graph 执行完成，session_id: {session_id}")

    except Exception as e:
        logger.error(f"流式 Chat Graph 执行失败: {e}")
        raise
