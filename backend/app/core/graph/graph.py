"""Graph 主文件 - 支持多 Agent 组合"""
import time
from typing import Dict, Any, AsyncGenerator
from langgraph.graph import StateGraph, START, END
from loguru import logger

from app.core.graph.state import ChatState
from app.core.graph.nodes.chat_agent_node import stream_chat_agent_node
from app.core.graph.nodes.rag_node import rag_node
from app.core.graph.nodes.history_node import history_manager_node
from app.core.graph.nodes.memory_node import memory_node
from app.core.graph.nodes.merge_node import merge_node



# 节点显示名称映射
NODE_DISPLAY_NAMES = {
    "rag": "RAG 检索",
    "memory": "长期记忆",
    "history_manager": "历史管理",
    "merge": "综合处理",
    "stream_chat_agent": "对话 Agent",
}

# 节点执行顺序定义（用于前端流程图渲染）
# 并行节点 rag/memory/history_manager 同时开始，merge 等待全部完成后执行
NODE_EXECUTION_ORDER = ["rag", "memory", "history_manager", "merge", "stream_chat_agent"]


def _summarize_node_input(node_name: str, state: ChatState) -> str:
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
        elif node_name == "merge":
            rag_ctx = state.get("rag_context")
            mem_ctx = state.get("memory_context")
            return f"RAG: {'有' if rag_ctx else '无'}, 记忆: {'有' if mem_ctx else '无'}"
        elif node_name == "stream_chat_agent":
            return f"输入: {user_input[:50]}" if user_input else "无输入"
        return ""
    except Exception:
        return ""


def _summarize_node_output(node_name: str, output: ChatState) -> str:
    """提取节点输出摘要（脱敏）"""
    try:
        if node_name == "rag":
            ctx = output.get("rag_context")
            if ctx:
                return f"检索到上下文，长度: {len(ctx)}"
            return "未检索到相关文档"
        elif node_name == "memory":
            ctx = output.get("memory_context")
            if ctx:
                return f"检索到记忆，长度: {len(ctx)}"
            return "无相关记忆"
        elif node_name == "history_manager":
            msgs = output.get("messages", [])
            return f"压缩后消息数: {len(msgs)}"
        elif node_name == "merge":
            ctx = output.get("context")
            if ctx:
                return f"合并后上下文，长度: {len(ctx)}"
            return "无可合并内容"
        elif node_name == "stream_chat_agent":
            resp = output.get("response", "")
            return f"回复长度: {len(resp)}" if resp else "无回复"
        return ""
    except Exception:
        return ""


def create_stream_chat_graph() -> StateGraph:
    """
    创建流式聊天 Graph

    拓扑：START → [rag, memory, history_manager] 并行 → merge → stream_chat_agent → END

    Returns:
        编译后的 StateGraph 实例
    """
    workflow = StateGraph(ChatState)

    # 添加节点
    workflow.add_node("rag", rag_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("history_manager", history_manager_node)
    workflow.add_node("merge", merge_node)
    workflow.add_node("stream_chat_agent", stream_chat_agent_node)

    # 三路并行：START 同时扇出到 rag / memory / history_manager
    workflow.add_edge(START, "rag")
    workflow.add_edge(START, "memory")
    workflow.add_edge(START, "history_manager")

    # 三路汇聚到 merge
    workflow.add_edge("rag", "merge")
    workflow.add_edge("memory", "merge")
    workflow.add_edge("history_manager", "merge")

    # merge → stream_chat_agent → END
    workflow.add_edge("merge", "stream_chat_agent")
    workflow.add_edge("stream_chat_agent", END)

    graph = workflow.compile()
    logger.info("流式 Chat Graph 创建成功（三路并行 + 综合处理）")
    return graph


# 创建全局流式 Graph 实例
stream_chat_graph = create_stream_chat_graph()



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
    initial_state = ChatState(
        messages=messages or [],
        user_input=user_input,
        rag_context=None,
        memory_context=None,
        context=None,
        session_id=session_id,
        user_id=user_id,
        response=""
    )

    workflow_start_time = time.time()
    node_timings: Dict[str, float] = {}  # 记录每个节点的完成时间
    completed_nodes: list = []  # 已完成的节点列表
    # 并行节点同时开始，merge 等待全部完成后执行
    parallel_nodes = ["rag", "memory", "history_manager"]
    node_order = ["rag", "memory", "history_manager", "merge", "stream_chat_agent"]
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
                        if node_name not in node_order:
                            continue

                        idx = node_order.index(node_name)

                        # 推断节点开始时间：
                        # 并行节点（rag/memory/history_manager）同时从 workflow_start_time 开始
                        # 串行节点（merge/stream_chat_agent）从上一个节点完成时间开始
                        if node_name in parallel_nodes:
                            start_time = workflow_start_time
                        else:
                            # merge 等待所有并行节点完成，stream_chat_agent 等待 merge
                            # 找到当前节点依赖的上一个节点完成时间
                            if last_completed_index >= 0:
                                start_time = node_timings.get(node_order[last_completed_index], workflow_start_time)
                            else:
                                start_time = workflow_start_time

                        # 发送 node_start 事件（让前端先渲染开始状态）
                        yield {
                            "type": "node_start",
                            "node": node_name,
                            "display_name": NODE_DISPLAY_NAMES.get(node_name, node_name),
                            "timestamp": start_time,
                        }

                        # 发送 node_end 事件
                        end_time = time.time()
                        if node_name in parallel_nodes:
                            # 并行节点：从 workflow_start_time 到完成的耗时
                            duration_ms = int((end_time - workflow_start_time) * 1000)
                        else:
                            # 串行节点：从上一个节点完成到当前的耗时
                            if last_completed_index >= 0:
                                prev_node = node_order[last_completed_index]
                                prev_end = node_timings.get(prev_node, workflow_start_time)
                                duration_ms = int((end_time - prev_end) * 1000)
                            else:
                                duration_ms = int((end_time - workflow_start_time) * 1000)

                        last_completed_index = idx
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
