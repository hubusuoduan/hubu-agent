"""Graph 主文件 - 支持多 Agent 组合"""
import time
from typing import Dict, Any, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from loguru import logger

from app.core.graph.state import ChatState
from app.core.graph.nodes.chat_agent_node import chat_agent_node, stream_chat_agent_node
from app.core.graph.nodes.rag_node import rag_node
from app.core.graph.nodes.history_node import history_manager_node
from app.core.graph.nodes.memory_node import memory_node
from app.core.graph.nodes.memory_extract_node import memory_extract_node


# 节点显示名称映射
NODE_DISPLAY_NAMES = {
    "rag": "RAG 检索",
    "memory": "长期记忆",
    "history_manager": "历史管理",
    "chat_agent": "对话 Agent",
    "stream_chat_agent": "对话 Agent",
    "memory_extract": "记忆提取",
}

# 节点执行顺序定义（用于前端流程图渲染）
NODE_EXECUTION_ORDER = ["rag", "memory", "history_manager", "stream_chat_agent", "memory_extract"]


def _summarize_node_input(node_name: str, state: dict) -> str:
    """提取节点输入摘要（脱敏）"""
    try:
        user_input = state.get("user_input", "")
        if node_name == "rag":
            return f"查询: {user_input[:50]}" if user_input else "无查询"
        elif node_name == "memory":
            user_id = state.get("user_id", "")
            return f"用户: {user_id[:8]}..." if user_id else "无用户ID"
        elif node_name == "history_manager":
            msg_count = len(state.get("messages", []))
            return f"消息数: {msg_count}"
        elif node_name in ("chat_agent", "stream_chat_agent"):
            return f"输入: {user_input[:50]}" if user_input else "无输入"
        elif node_name == "memory_extract":
            resp = state.get("response", "")
            return f"回复长度: {len(resp)}" if resp else "无回复"
        return ""
    except Exception:
        return ""


def _summarize_node_output(node_name: str, output: dict) -> str:
    """提取节点输出摘要（脱敏）"""
    try:
        if node_name == "rag":
            ctx = output.get("context")
            if ctx:
                return f"检索到上下文，长度: {len(ctx)}"
            return "未检索到相关文档"
        elif node_name == "memory":
            ctx = output.get("context")
            if ctx:
                return f"记忆已注入，上下文长度: {len(ctx)}"
            return "无相关记忆"
        elif node_name == "history_manager":
            msgs = output.get("messages", [])
            return f"压缩后消息数: {len(msgs)}"
        elif node_name in ("chat_agent", "stream_chat_agent"):
            resp = output.get("response", "")
            return f"回复长度: {len(resp)}" if resp else "无回复"
        elif node_name == "memory_extract":
            return "记忆提取完成"
        return ""
    except Exception:
        return ""


def create_chat_graph() -> StateGraph:
    """
    创建聊天 Graph

    Returns:
        编译后的 StateGraph 实例
    """
    workflow = StateGraph(ChatState)

    workflow.add_node("rag", rag_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("history_manager", history_manager_node)
    workflow.add_node("chat_agent", chat_agent_node)
    workflow.add_node("memory_extract", memory_extract_node)

    workflow.add_edge(START, "rag")
    workflow.add_edge("rag", "memory")
    workflow.add_edge("memory", "history_manager")
    workflow.add_edge("history_manager", "chat_agent")
    workflow.add_edge("chat_agent", "memory_extract")
    workflow.add_edge("memory_extract", END)

    graph = workflow.compile()
    logger.info("Chat Graph 创建成功（包含 RAG 节点、长期记忆节点和历史管理节点）")
    return graph


def create_stream_chat_graph() -> StateGraph:
    """
    创建流式聊天 Graph

    Returns:
        编译后的 StateGraph 实例
    """
    workflow = StateGraph(ChatState)

    workflow.add_node("rag", rag_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("history_manager", history_manager_node)
    workflow.add_node("stream_chat_agent", stream_chat_agent_node)
    workflow.add_node("memory_extract", memory_extract_node)

    workflow.add_edge(START, "rag")
    workflow.add_edge("rag", "memory")
    workflow.add_edge("memory", "history_manager")
    workflow.add_edge("history_manager", "stream_chat_agent")
    workflow.add_edge("stream_chat_agent", "memory_extract")
    workflow.add_edge("memory_extract", END)

    graph = workflow.compile()
    logger.info("流式 Chat Graph 创建成功（包含 RAG 节点、长期记忆节点和历史管理节点）")
    return graph


# 创建全局 Graph 实例
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
        initial_state = {
            "messages": messages or [],
            "user_input": user_input,
            "context": None,
            "session_id": session_id,
            "user_id": user_id,
            "response": ""
        }

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
        initial_state = {
            "messages": messages or [],
            "user_input": user_input,
            "context": None,
            "session_id": session_id,
            "user_id": user_id,
            "response": ""
        }

        async for chunk in stream_chat_graph.astream(initial_state, stream_mode="custom"):
            if isinstance(chunk, dict):
                yield chunk
            elif isinstance(chunk, str) and chunk:
                yield {"type": "content", "content": chunk}

        logger.info(f"流式 Chat Graph 执行完成，session_id: {session_id}")

    except Exception as e:
        logger.error(f"流式 Chat Graph 执行失败: {e}")
        raise


async def run_stream_chat_graph_with_trace(
    user_input: str,
    session_id: str = "default",
    user_id: str = "",
    messages: list = None
) -> AsyncGenerator[dict, None]:
    """
    带节点追踪的流式运行聊天 Graph

    在流式输出的基础上，额外推送节点执行状态事件：
    - node_start: 节点开始执行
    - node_end: 节点执行完成（含耗时和输入/输出摘要）
    - node_error: 节点执行失败
    - workflow_done: 整个工作流执行完成

    Args:
        user_input: 用户输入
        session_id: 会话ID
        user_id: 用户ID（用于长期记忆）
        messages: 历史消息列表（可选）

    Yields:
        结构化事件字典，包含节点追踪信息和内容流
    """
    initial_state = {
        "messages": messages or [],
        "user_input": user_input,
        "context": None,
        "session_id": session_id,
        "user_id": user_id,
        "response": ""
    }

    workflow_start_time = time.time()
    node_timings: Dict[str, float] = {}  # 记录每个节点的开始时间
    completed_nodes: list = []  # 已完成的节点列表
    # 跟踪上一个完成的节点，用于推断当前正在执行的节点
    node_order = ["rag", "memory", "history_manager", "stream_chat_agent", "memory_extract"]
    last_completed_index = -1

    try:
        # 使用双模式流：updates 获取节点完成事件，custom 获取流式内容
        async for mode, chunk in stream_chat_graph.astream(
            initial_state,
            stream_mode=["updates", "custom"]
        ):
            if mode == "updates":
                # updates 模式：每个节点执行完毕后输出 {node_name: output_state}
                if isinstance(chunk, dict):
                    for node_name, node_output in chunk.items():
                        # 推断当前节点的开始时间：
                        # 当前节点 = 上一个节点完成后开始执行
                        if node_name in node_order:
                            idx = node_order.index(node_name)
                            # 发送之前跳过的节点的 node_end（未执行但被跳过的情况不需要处理）
                            # 记录当前节点的开始时间 = 上一个节点完成的时间
                            if last_completed_index >= 0:
                                start_time = node_timings.get(node_order[last_completed_index], workflow_start_time)
                            else:
                                start_time = workflow_start_time

                            # 发送 node_start 事件（在 node_end 之前，让前端先渲染开始状态）
                            yield {
                                "type": "node_start",
                                "node": node_name,
                                "display_name": NODE_DISPLAY_NAMES.get(node_name, node_name),
                                "timestamp": start_time,
                            }

                        # 发送 node_end 事件
                        end_time = time.time()
                        # 使用 workflow_start_time 到 end_time 的差值作为第一个节点的耗时
                        # 后续节点使用上一个节点完成到当前的时间差
                        if node_name in node_order:
                            idx = node_order.index(node_name)
                            if last_completed_index < 0:
                                duration_ms = int((end_time - workflow_start_time) * 1000)
                            else:
                                prev_node = node_order[last_completed_index]
                                prev_end = node_timings.get(prev_node, workflow_start_time)
                                duration_ms = int((end_time - prev_end) * 1000)
                            last_completed_index = idx
                        else:
                            duration_ms = 0

                        node_timings[node_name] = end_time
                        input_summary = _summarize_node_input(node_name, initial_state)
                        output_summary = _summarize_node_output(node_name, node_output or {})

                        completed_nodes.append(node_name)

                        yield {
                            "type": "node_end",
                            "node": node_name,
                            "display_name": NODE_DISPLAY_NAMES.get(node_name, node_name),
                            "duration_ms": duration_ms,
                            "input_summary": input_summary,
                            "output_summary": output_summary,
                            "timestamp": end_time,
                        }

            elif mode == "custom":
                # custom 模式：流式内容输出（来自 stream_chat_agent_node 的 writer）
                if isinstance(chunk, dict):
                    yield chunk
                elif isinstance(chunk, str) and chunk:
                    yield {"type": "content", "content": chunk}

        # 工作流完成
        total_duration_ms = int((time.time() - workflow_start_time) * 1000)
        yield {
            "type": "workflow_done",
            "nodes": completed_nodes,
            "total_duration_ms": total_duration_ms,
            "timestamp": time.time(),
        }

        logger.info(f"带追踪的流式 Chat Graph 执行完成，session_id: {session_id}，耗时: {total_duration_ms}ms")

    except Exception as e:
        logger.error(f"带追踪的流式 Chat Graph 执行失败: {e}")
        yield {
            "type": "node_error",
            "node": "unknown",
            "error": str(e),
            "timestamp": time.time(),
        }
        raise
