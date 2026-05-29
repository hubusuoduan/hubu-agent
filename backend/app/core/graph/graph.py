"""Graph 主文件 - 多 Agent 协作拓扑

拓扑结构:
START → [rag, memory, history_manager] 并行 → merge → supervisor（任务规划+调度）
                                                           │
                                                 ┌─────────┼─────────┬──────────┐──────────┐
                                                 ▼         ▼         ▼          ▼          ▼
                                               chat    researcher  coder     skill    用户Agent...
                                                 │         │         │          │          │
                                                 └─────────┴─────────┴──────────┘──────────┘
                                                           │
                                                           ▼
                                                       reviewer
                                                      ╱    |    ╲
                                               通过 ✅  推进 ➡️  重试 🔁
                                                  │        │        │
                                                  ▼        └→ supervisor（推进下一步）
                                                 END                └→ supervisor（重新规划）

Supervisor 制定任务计划（如 ["researcher", "skill"]），按步骤调度 Agent。
Reviewer 判断：advance → Supervisor 推进下一步，retry → Supervisor 重新规划，pass → END。

注意: memory_extract 已从 graph 中移除，改为 reviewer 通过后异步后台执行，
避免记忆提取耗时阻塞工作流结束。

用户自建 Agent 通过 create_stream_chat_graph(user_agents) 动态注入，
运行时循环 add_node + add_edge 连接到 supervisor 和 reviewer。
"""
import time
from typing import Dict, Any, AsyncGenerator, List, Optional
from langgraph.graph import StateGraph, START, END
from loguru import logger

from app.core.graph.state import ChatState
from app.core.graph.nodes.rag_node import rag_node
from app.core.graph.nodes.memory_node import memory_node
from app.core.graph.nodes.history_node import history_manager_node
from app.core.graph.nodes.merge_node import merge_node
from app.core.graph.nodes.supervisor_node import supervisor_node
from app.core.graph.nodes.chat_agent_node import chat_agent_node
from app.core.graph.nodes.researcher_node import researcher_node
from app.core.graph.nodes.coder_node import coder_node
from app.core.graph.nodes.skill_node import skill_node
from app.core.graph.nodes.reviewer_node import reviewer_node
from app.core.agents.llm import MemoryExtractAgent
from app.core.agents.custom import AgentConfig, make_user_agent_node


# 节点显示名称映射（系统 Agent 固定部分）
NODE_DISPLAY_NAMES = {
    "rag": "RAG 检索",
    "memory": "长期记忆",
    "history_manager": "历史管理",
    "merge": "综合处理",
    "supervisor": "意图路由",
    "chat": "对话 Agent",
    "researcher": "信息检索 Agent",
    "coder": "代码执行 Agent",
    "skill": "技能执行 Agent",
    "reviewer": "审查 Agent",
}

# 节点执行顺序定义（用于前端流程图渲染，系统固定部分）
NODE_EXECUTION_ORDER = [
    "rag", "memory", "history_manager", "merge", "supervisor",
    "chat", "researcher", "coder", "skill",
    "reviewer"
]

# 并行节点
PARALLEL_NODES = ["rag", "memory", "history_manager"]

# 系统 Agent 节点（固定）
SYSTEM_AGENT_NODES = ["chat", "researcher", "coder", "skill"]

# Agent 节点（兼容旧代码，运行时会动态扩展）
AGENT_NODES = ["chat", "researcher", "coder", "skill"]


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
        elif node_name == "supervisor":
            retry = state.get("retry_count", 0)
            feedback = state.get("review_feedback", "")
            if feedback:
                return f"审查反馈: {feedback[:50]} (重试: {retry})"
            return f"输入: {user_input[:50]}"
        elif node_name in AGENT_NODES or node_name.startswith("user_"):
            scratchpad = state.get("agent_scratchpad", [])
            return f"已执行: {len(scratchpad)} 个Agent"
        elif node_name == "reviewer":
            resp = state.get("response", "")
            return f"审查回复，长度: {len(resp)}"
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
        elif node_name == "supervisor":
            next_agent = output.get("next_agent", "")
            task_plan = output.get("task_plan", state.get("task_plan", []))
            plan_index = output.get("plan_index", state.get("plan_index", 0))
            task_instruction = output.get("task_instruction", "")
            if task_plan and len(task_plan) > 1:
                plan_summary = " → ".join(
                    s.get("agent", "?") if isinstance(s, dict) else str(s)
                    for s in task_plan
                )
                return f"计划: {plan_summary}，当前: {next_agent} ({plan_index + 1}/{len(task_plan)})"
            if task_instruction:
                return f"路由到: {next_agent} — {task_instruction[:50]}"
            return f"路由到: {next_agent}"
        elif node_name in AGENT_NODES or node_name.startswith("user_"):
            resp = output.get("response", "")
            return f"回复长度: {len(resp)}" if resp else "无回复"
        elif node_name == "reviewer":
            result = output.get("review_result", "")
            feedback = output.get("review_feedback", "")
            if result == "pass":
                return "审查通过 ✅"
            elif result == "advance":
                plan = output.get("task_plan", state.get("task_plan", []))
                idx = output.get("plan_index", state.get("plan_index", 0))
                next_step = plan[idx + 1] if idx + 1 < len(plan) else "?"
                return f"推进 ➡️ 下一步: {next_step}"
            return f"需要补充 🔁: {feedback[:50]}"
        return ""
    except Exception:
        return ""


def _route_after_supervisor(state: ChatState) -> str:
    """Supervisor 之后的条件路由：根据 next_agent 决定走向哪个 Agent

    支持系统 Agent 和用户自建 Agent 的动态路由。
    """
    next_agent = state.get("next_agent", "chat")
    # 检查是否在系统 Agent 列表中
    if next_agent in SYSTEM_AGENT_NODES:
        return next_agent
    # 检查是否是用户自建 Agent（user_ 前缀）
    if next_agent.startswith("user_"):
        return next_agent
    # 兼容旧的 AGENT_NODES 列表
    if next_agent in AGENT_NODES:
        return next_agent
    logger.warning(f"Supervisor 路由到未知 Agent: {next_agent}，降级为 chat")
    return "chat"


async def _background_memory_extract(state: ChatState) -> None:
    """后台异步执行记忆提取（fire-and-forget）

    编排逻辑：
    1. 检查 user_id / response，缺少则跳过
    2. 读取用户已有记忆（去重用）
    3. 调用 MemoryExtractAgent 提取（纯 LLM）
    4. 写入 Milvus

    不阻塞工作流，失败也不影响主流程。
    """
    try:
        user_id = state.get("user_id", "")
        response = state.get("response", "")
        session_id = state.get("session_id", "default")

        # 缺少必要信息则跳过
        if not user_id or not response:
            logger.debug("缺少 user_id 或 response，跳过记忆提取")
            return

        # 读取用户已有记忆，用于 LLM 层面去重
        from app.services.memory_service import get_memory_service
        memory_service = get_memory_service()
        existing_result = await memory_service.list_memories(user_id=user_id, limit=50)
        existing_contents = [m.get("content", "") for m in existing_result.get("items", [])]

        # 调用 Agent 提取记忆（纯 LLM 调用），已有记忆通过参数传入而非污染 state
        memories = await MemoryExtractAgent.extract(state, existing_memories=existing_contents)

        if not memories:
            return

        # 写入 Milvus
        for m in memories:
            await memory_service.add_memory(
                user_id=user_id,
                content=m["content"],
                memory_type=m["type"],
                source_dialog_id=session_id,
                importance=m.get("importance", 3)
            )

        logger.info(f"后台记忆提取完成，写入 {len(memories)} 条记忆，user={user_id}")
    except Exception as e:
        logger.error(f"后台记忆提取失败（不影响主流程）: {e}")


def _route_after_reviewer(state: ChatState) -> str:
    """Reviewer 之后的条件路由：通过 → END，推进/重试 → supervisor"""
    review_result = state.get("review_result", "pass")
    if review_result in ("retry", "advance"):
        return "supervisor"
    return END


def create_stream_chat_graph(user_agents: List[AgentConfig] = None) -> StateGraph:
    """
    创建多 Agent 协作 Graph（支持动态注入用户自建 Agent）

    拓扑：
    START → [rag, memory, history_manager] 并行 → merge → supervisor（循环路由）
    supervisor → chat / researcher / coder / writer / 用户Agent... → reviewer
    reviewer → pass → END
    reviewer → retry → supervisor（循环）

    Args:
        user_agents: 用户自建 Agent 配置列表，为 None 或空则只有系统 Agent

    Returns:
        编译后的 StateGraph 实例
    """
    workflow = StateGraph(ChatState)

    # ========== 添加节点 ==========

    # 前置节点
    workflow.add_node("rag", rag_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("history_manager", history_manager_node)
    workflow.add_node("merge", merge_node)

    # Supervisor
    workflow.add_node("supervisor", supervisor_node)

    # 系统 Agent（固定）
    workflow.add_node("chat", chat_agent_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("skill", skill_node)

    # 用户自建 Agent（动态注入）
    user_agent_names = []
    if user_agents:
        for config in user_agents:
            node_name = config.node_name  # "user_{name}"
            workflow.add_node(node_name, make_user_agent_node(config))
            user_agent_names.append(node_name)
            # 显示名称在 run_stream_chat_graph_with_trace 中动态构建
            # 不再修改全局 NODE_DISPLAY_NAMES，避免并发覆盖
        logger.info(f"动态注入 {len(user_agents)} 个用户 Agent: {user_agent_names}")

    # Reviewer
    workflow.add_node("reviewer", reviewer_node)

    # ========== 添加边 ==========

    # 三路并行：START 同时扇出到 rag / memory / history_manager
    workflow.add_edge(START, "rag")
    workflow.add_edge(START, "memory")
    workflow.add_edge(START, "history_manager")

    # 三路汇聚到 merge
    workflow.add_edge("rag", "merge")
    workflow.add_edge("memory", "merge")
    workflow.add_edge("history_manager", "merge")

    # merge → supervisor
    workflow.add_edge("merge", "supervisor")

    # supervisor → 条件路由到所有 Agent（系统 + 用户自建）
    route_map = {
        "chat": "chat",
        "researcher": "researcher",
        "coder": "coder",
        "skill": "skill",
    }
    for name in user_agent_names:
        route_map[name] = name
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        route_map,
    )

    # 系统 Agent → reviewer
    for name in SYSTEM_AGENT_NODES:
        workflow.add_edge(name, "reviewer")

    # 用户 Agent → reviewer（循环加边！）
    for name in user_agent_names:
        workflow.add_edge(name, "reviewer")

    # reviewer → 条件路由：通过 → END，不够 → supervisor
    workflow.add_conditional_edges(
        "reviewer",
        _route_after_reviewer,
        {
            END: END,
            "supervisor": "supervisor",
        }
    )

    graph = workflow.compile()
    logger.info(f"多 Agent 协作 Graph 创建成功（系统 Agent: 4, 用户 Agent: {len(user_agent_names)}）")
    return graph





async def run_stream_chat_graph_with_trace(
    user_input: str,
    session_id: str = "default",
    user_id: str = "",
    messages: list = None,
    user_agents: List[AgentConfig] = None,
) -> AsyncGenerator[dict, None]:
    """
    带节点追踪的流式运行聊天 Graph（支持动态注入用户自建 Agent）

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
        user_agents: 用户自建 Agent 配置列表（可选，动态注入）

    Yields:
        结构化事件字典，包含节点追踪信息和内容流
    """
    # 构建用户 Agent 描述（注入 state 供 Supervisor 使用）
    user_agents_desc = []
    if user_agents:
        user_agents_desc = [
            {"name": c.node_name, "display_name": c.display_name, "description": c.description}
            for c in user_agents
        ]

    initial_state = ChatState(
        messages=messages or [],
        user_input=user_input,
        rag_context=None,
        memory_context=None,
        context=None,
        session_id=session_id,
        user_id=user_id,
        response="",
        next_agent="",
        task_plan=[],
        task_instruction="",
        plan_index=0,
        review_result="",
        review_feedback="",
        retry_count=0,
        agent_scratchpad=[],
        user_agents_desc=user_agents_desc,
    )

    workflow_start_time = time.time()
    node_timings: Dict[str, float] = {}
    completed_nodes: list = []
    last_completed_index = -1
    # 累积状态：逐步合并每个节点的输出，保持完整上下文
    accumulated_state: Dict[str, Any] = dict(initial_state)

    # 动态构建节点显示名称和执行顺序（支持用户自建 Agent）
    display_names = dict(NODE_DISPLAY_NAMES)
    execution_order = list(NODE_EXECUTION_ORDER)
    if user_agents:
        for config in user_agents:
            display_names[config.node_name] = config.display_name
            # 在 reviewer 之前插入用户 Agent
            if config.node_name not in execution_order:
                execution_order.insert(-1, config.node_name)  # -1 是 reviewer 的位置

    try:
        # 每次请求重新构建 Graph（用户 Agent 配置可能随时变更）
        graph = create_stream_chat_graph(user_agents)

        # 使用双模式流：updates 获取节点完成事件，custom 获取流式内容
        async for mode, chunk in graph.astream(
            initial_state,
            stream_mode=["updates", "custom"]
        ):
            if mode == "updates":
                # updates 模式：每个节点执行完毕后输出 {node_name: output_state}
                if isinstance(chunk, dict):
                    for node_name, node_output in chunk.items():
                        # 推断节点开始时间
                        if node_name in PARALLEL_NODES:
                            start_time = workflow_start_time
                        else:
                            if last_completed_index >= 0:
                                prev_node = execution_order[last_completed_index] if last_completed_index < len(execution_order) else None
                                start_time = node_timings.get(prev_node, workflow_start_time) if prev_node else workflow_start_time
                            else:
                                start_time = workflow_start_time

                        # 发送 node_start 事件
                        yield {
                            "type": "node_start",
                            "node": node_name,
                            "display_name": display_names.get(node_name, node_name),
                            "timestamp": start_time,
                        }

                        # 发送 node_end 事件
                        end_time = time.time()
                        if node_name in PARALLEL_NODES:
                            duration_ms = int((end_time - workflow_start_time) * 1000)
                        else:
                            if last_completed_index >= 0 and last_completed_index < len(execution_order):
                                prev_node = execution_order[last_completed_index]
                                prev_end = node_timings.get(prev_node, workflow_start_time)
                                duration_ms = int((end_time - prev_end) * 1000)
                            else:
                                duration_ms = int((end_time - workflow_start_time) * 1000)

                        # 更新执行顺序索引
                        if node_name in execution_order:
                            last_completed_index = execution_order.index(node_name)

                        node_timings[node_name] = end_time
                        input_summary = _summarize_node_input(node_name, accumulated_state)
                        output_summary = _summarize_node_output(node_name, node_output or {})

                        # 累积合并节点输出到完整状态
                        if isinstance(node_output, dict):
                            for k, v in node_output.items():
                                # messages 使用 add_messages 语义追加，其他直接覆盖
                                if k == "messages" and k in accumulated_state:
                                    from langgraph.graph.message import add_messages
                                    accumulated_state[k] = add_messages(accumulated_state[k], v)
                                elif k == "agent_scratchpad" and k in accumulated_state:
                                    accumulated_state[k] = accumulated_state[k] + v
                                else:
                                    accumulated_state[k] = v

                        completed_nodes.append(node_name)

                        yield {
                            "type": "node_end",
                            "node": node_name,
                            "display_name": display_names.get(node_name, node_name),
                            "duration_ms": duration_ms,
                            "input_summary": input_summary,
                            "output_summary": output_summary,
                            "timestamp": end_time,
                        }

                        # reviewer 通过后，异步后台执行记忆提取（不阻塞工作流）
                        if node_name == "reviewer" and isinstance(node_output, dict):
                            if node_output.get("review_result") != "retry":
                                import asyncio
                                # 使用累积的完整状态，包含所有中间节点的输出
                                asyncio.create_task(_background_memory_extract(dict(accumulated_state)))

            elif mode == "custom":
                # custom 模式：流式内容输出（来自各 Agent 节点的 writer）
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

        logger.info(f"多 Agent Graph 执行完成，session_id: {session_id}，耗时: {total_duration_ms}ms，节点: {completed_nodes}")

    except Exception as e:
        logger.error(f"多 Agent Graph 执行失败: {e}")
        yield {
            "type": "node_error",
            "node": "unknown",
            "error": str(e),
            "timestamp": time.time(),
        }
        raise

