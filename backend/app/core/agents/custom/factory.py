"""用户自建 Agent 节点工厂 - 动态生成 LangGraph 节点函数

生成的节点函数和系统 Agent 节点（如 researcher_node）同构：
- 接收 (state, writer) 参数
- 返回 {"response": ..., "agent_scratchpad": [...]}
- 支持流式输出和事件转发
"""
from langgraph.prebuilt import create_react_agent
from langgraph.types import StreamWriter
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

from app.core.graph.state import ChatState
from app.core.agents.custom.loader import AgentConfig
from app.core.agents.bases.base_react_agent import BaseReactAgent
from app.services.llm_service import LLMService
from app.middleware.user_context import current_user_id
from app.utils.format import format_tool_display_name

# scratchpad 中每条 Agent 输出的最大字符数
SCRATCHPAD_MAX_OUTPUT = 1000

# 动态 Agent 实例缓存 {cache_key: agent_executor}
_dynamic_agent_cache: dict = {}


def _get_agent_max_iterations() -> int:
    """从用户配置获取 Agent 最大迭代次数"""
    try:
        from app.services.settings_service import SettingsFactory
        return SettingsFactory.get(key="AGENT_MAX_ITERATIONS")
    except Exception:
        pass
    return 10  # 默认值


async def _get_or_create_dynamic_agent(
    config: AgentConfig,
    session_id: str,
) -> object:
    """获取或创建动态 Agent 实例（按 config.name + session_id 缓存）"""
    cache_key = f"dynamic_{config.name}_{session_id}"
    if cache_key not in _dynamic_agent_cache:
        model = await LLMService.get_model_async()
        tools = config.resolved_tools
        _dynamic_agent_cache[cache_key] = create_react_agent(
            model=model,
            tools=tools,
            prompt=config.system_prompt,
        )
        logger.info(f"创建动态 Agent 实例: {config.name}, session: {session_id}, 工具: {config.tools}")
    return _dynamic_agent_cache[cache_key]


def make_user_agent_node(agent_config: AgentConfig):
    """为用户自建 Agent 生成节点函数

    Args:
        agent_config: Agent 配置（从 AGENT.md 解析而来）

    Returns:
        异步节点函数，签名和 researcher_node 等一致
    """
    async def user_agent_node(state: ChatState, writer: StreamWriter) -> dict:
        """用户自建 Agent 节点"""
        # 构建输入消息（复用 BaseReactAgent 的逻辑）
        user_input = state.get("user_input", "")
        context = state.get("context")
        messages = state.get("messages", [])
        review_feedback = state.get("review_feedback", "")
        agent_scratchpad = state.get("agent_scratchpad", [])

        input_messages = BaseReactAgent.build_input_messages(
            user_input=user_input,
            context=context,
            messages=messages,
            review_feedback=review_feedback,
            agent_scratchpad=agent_scratchpad,
        )

        # 获取 Agent 实例
        agent = await _get_or_create_dynamic_agent(
            config=agent_config,
            session_id=state.get("session_id", "default"),
        )

        from app.callbacks import usage_metadata_callback

        # 流式执行（和 BaseReactAgent.stream_run 逻辑一致）
        full_response = ""
        async for event in agent.astream_events(
            {"messages": input_messages},
            version="v2",
            config={
                "recursion_limit": _get_agent_max_iterations(),
                "callbacks": [usage_metadata_callback],
            }
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # thinking 内容
                reasoning = None
                if hasattr(chunk, "additional_kwargs"):
                    reasoning = chunk.additional_kwargs.get("reasoning_content")
                if reasoning:
                    writer({"type": "thinking", "content": reasoning})
                # 正常文本
                content = chunk.content if hasattr(chunk, "content") else ""
                if content and content.strip() and not content.strip().startswith("<tool_call"):
                    full_response += content
                    writer({"type": "content", "content": content})

            elif kind == "on_chat_model_start":
                writer({"type": "thinking", "content": f"正在思考（{agent_config.display_name}）..."})

            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = ""
                try:
                    tool_input = str(event.get("data", {}).get("input", ""))[:500]
                except Exception:
                    pass
                display_name = format_tool_display_name(tool_name)
                writer({
                    "type": "event",
                    "data": {
                        "title": f"执行工具: {display_name}",
                        "status": "START",
                        "message": f"正在调用工具 {display_name}..." + (f"\n输入: {tool_input}" if tool_input else ""),
                        "tool_name": tool_name
                    }
                })

            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                tool_output = ""
                try:
                    output = event.get("data", {}).get("output", "")
                    if hasattr(output, "content"):
                        tool_output = str(output.content)[:2000]
                    else:
                        tool_output = str(output)[:2000]
                except Exception:
                    tool_output = "工具执行完成"
                display_name = format_tool_display_name(tool_name)
                writer({
                    "type": "event",
                    "data": {
                        "title": f"执行工具: {display_name}",
                        "status": "END",
                        "message": tool_output,
                        "tool_name": tool_name
                    }
                })

        logger.info(f"用户 Agent {agent_config.name} 执行完成，回复长度: {len(full_response)}")

        return {
            "response": full_response,
            "agent_scratchpad": [{"agent": agent_config.name, "output": full_response[:SCRATCHPAD_MAX_OUTPUT]}],
        }

    # 设置函数名，方便调试和日志
    user_agent_node.__name__ = f"{agent_config.node_name}_node"
    user_agent_node.__qualname__ = f"{agent_config.node_name}_node"

    return user_agent_node


def clear_dynamic_cache(session_id: str = None):
    """清除动态 Agent 缓存

    Args:
        session_id: 指定 session 则只清该 session 的缓存，否则清全部
    """
    global _dynamic_agent_cache
    if session_id:
        keys_to_remove = [k for k in _dynamic_agent_cache if session_id in k]
        for k in keys_to_remove:
            del _dynamic_agent_cache[k]
        logger.info(f"清除动态 Agent 缓存: session={session_id}, 数量: {len(keys_to_remove)}")
    else:
        _dynamic_agent_cache.clear()
        logger.info("清除所有动态 Agent 缓存")
