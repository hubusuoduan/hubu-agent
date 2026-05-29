"""ReAct Agent 基类 - 封装 ReAct Agent 的公共逻辑"""
from typing import Dict, List, Optional
from loguru import logger
from langgraph.prebuilt import create_react_agent
from langgraph.types import StreamWriter
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import BaseTool

from app.core.graph.state import ChatState
from app.services.llm_service import LLMService
from app.prompts import load_prompt
from app.utils.format import format_tool_display_name
from app.middleware.user_context import current_user_id


class BaseReactAgent:
    """ReAct Agent 基类

    封装 ReAct Agent 的公共逻辑：
    - 实例创建与缓存
    - 输入消息构建（上下文注入、历史消息、审查反馈、前置 Agent 结果）
    - 流式执行与事件转发

    子类只需定义：
    - name: Agent 名称
    - prompt_name: prompt 文件名
    - tools: 工具列表
    - thinking_hint: 思考提示语
    """

    name: str = "base_react"
    prompt_name: str = "chat_agent"
    tools: List[BaseTool] = []
    thinking_hint: str = "正在思考..."

    # 全局实例缓存 {session_id: agent_executor}
    _agent_cache: Dict[str, object] = {}

    def __init_subclass__(cls, **kwargs):
        """子类定义时，自动为其创建独立的 _agent_cache"""
        super().__init_subclass__(**kwargs)
        cls._agent_cache = {}

    @classmethod
    def _get_agent_max_iterations(cls) -> int:
        """从用户配置获取 Agent 最大迭代次数"""
        try:
            from app.services.settings_service import SettingsFactory
            return SettingsFactory.get(key="AGENT_MAX_ITERATIONS")
        except Exception:
            pass
        return 10  # 默认值

    @classmethod
    async def get_or_create_agent(cls, session_id: str) -> object:
        """获取或创建 Agent 实例（按 session_id 缓存）"""
        if session_id not in cls._agent_cache:
            model = await LLMService.get_model_async()
            system_prompt = load_prompt(cls.prompt_name)
            cls._agent_cache[session_id] = create_react_agent(
                model=model,
                tools=cls.tools,
                prompt=system_prompt
            )
            logger.info(f"创建新 {cls.name} Agent 实例: {session_id}")
        return cls._agent_cache[session_id]

    @classmethod
    def build_input_messages(
        cls,
        user_input: str,
        context: Optional[str] = None,
        messages: Optional[list] = None,
        review_feedback: Optional[str] = None,
        agent_scratchpad: Optional[list] = None,
    ) -> list:
        """构建输入消息列表

        将上下文、历史消息、前置 Agent 结果、审查反馈
        按统一格式组装为 LangChain 消息列表。

        Args:
            user_input: 用户输入
            context: RAG + 记忆的合并上下文
            messages: 历史消息（LangChain 消息格式）
            review_feedback: Reviewer 审查反馈
            agent_scratchpad: 前置 Agent 的执行记录

        Returns:
            构建好的消息列表
        """
        input_messages = []

        # 1. 注入上下文（RAG检索结果 + 长期记忆）
        if context:
            input_messages.append(HumanMessage(
                content=f"[参考信息]\n{context}\n\n---\n\n请结合以上参考信息回答我的后续问题。"
            ))
            input_messages.append(AIMessage(
                content="好的，我会结合以上参考信息来回答你的问题。"
            ))

        # 2. 注入之前 Agent 的执行结果
        if agent_scratchpad:
            from app.utils.text import format_scratchpad
            scratch_text = format_scratchpad(
                agent_scratchpad, max_output=2000,
                fmt="[{name}的输出]\n{output}", separator="\n"
            )
            input_messages.append(HumanMessage(
                content=f"[之前 Agent 的执行结果]\n{scratch_text}\n\n---\n\n请基于以上信息继续完成任务。"
            ))
            input_messages.append(AIMessage(
                content="好的，我会基于之前 Agent 的结果继续完成任务。"
            ))

        # 3. 添加历史消息
        if messages:
            for msg in messages:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    if msg.type == "system":
                        continue
                    if msg.type == "human":
                        input_messages.append(HumanMessage(content=msg.content))
                    else:
                        input_messages.append(AIMessage(content=msg.content))

        # 4. 构建当前输入（附带审查反馈）
        current_input = user_input
        if review_feedback:
            current_input = f"[审查反馈: {review_feedback}]\n\n{user_input}"
        input_messages.append(HumanMessage(content=current_input))

        return input_messages

    @classmethod
    async def stream_run(
        cls,
        state: ChatState,
        writer: StreamWriter,
    ) -> dict:
        """流式执行 Agent，通过 writer 转发事件

        Args:
            state: Graph 状态
            writer: LangGraph StreamWriter

        Returns:
            更新后的状态字典，包含 response 和 agent_scratchpad
        """
        user_input = state.get("user_input", "")
        context = state.get("context")
        messages = state.get("messages", [])
        review_feedback = state.get("review_feedback", "")
        agent_scratchpad = state.get("agent_scratchpad", [])

        # 构建输入消息
        input_messages = cls.build_input_messages(
            user_input=user_input,
            context=context,
            messages=messages,
            review_feedback=review_feedback,
            agent_scratchpad=agent_scratchpad,
        )

        # 获取 Agent 实例
        agent = await cls.get_or_create_agent(state.get("session_id", "default"))

        from app.callbacks import usage_metadata_callback

        # 流式执行
        full_response = ""
        async for event in agent.astream_events(
            {"messages": input_messages},
            version="v2",
            config={
                "recursion_limit": cls._get_agent_max_iterations(),
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
                writer({"type": "thinking", "content": cls.thinking_hint})

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

        logger.info(f"{cls.name} Agent 执行完成，回复长度: {len(full_response)}")

        return full_response
