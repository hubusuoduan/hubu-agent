"""基于 LangChain 的聊天智能体实现"""
from typing import List, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from loguru import logger
from app.prompts import load_prompt
from app.utils.format import format_tool_display_name


class ChatAgent:
    """基于 LangChain 的聊天智能体"""

    def __init__(self, model: ChatOpenAI, system_prompt: Optional[str] = None, tools: Optional[List[BaseTool]] = None):
        """
        初始化 ChatAgent

        Args:
            model: LLM模型实例
            system_prompt: 系统提示词
            tools: 工具列表（可选）
        """
        self.model = model
        self.system_prompt = system_prompt or load_prompt("chat_agent")

        self.tools = tools or []

        # 使用 create_react_agent 创建 Agent Executor
        from app.config import settings
        self.agent_executor = create_react_agent(
            model=model,
            tools=self.tools,
            prompt=self.system_prompt
        )

        # 设置最大迭代次数，防止工具调用死循环
        self.agent_max_iterations = settings.AGENT_MAX_ITERATIONS

        logger.info(f"ChatAgent 初始化成功，加载了 {len(self.tools)} 个工具")

    def _build_messages(
        self,
        user_input: str,
        history: Optional[List[dict]] = None,
        context: Optional[str] = None
    ) -> list:
        """构建输入消息列表

        将 context（RAG检索结果 + 长期记忆）作为对话前缀注入，
        确保 LLM 能够看到参考信息。

        Args:
            user_input: 用户输入
            history: 历史消息列表
            context: RAG检索的上下文信息（可选）

        Returns:
            构建好的消息列表
        """
        messages = []

        # 如果有 context（RAG检索结果 + 长期记忆），作为对话前缀注入
        # 这样可以绕过 create_react_agent 的固定 prompt 限制
        if context:
            messages.append(HumanMessage(
                content=f"[参考信息]\n{context}\n\n---\n\n请结合以上参考信息回答我的后续问题。"
            ))
            messages.append(AIMessage(
                content="好的，我会结合以上参考信息来回答你的问题。"
            ))

        # 添加历史消息
        if history and len(history) > 0:
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg.get("role") == "system":
                    # system消息已经在agent_executor的prompt中处理
                    pass

        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))

        return messages

    async def stream_run(self, user_input: str, history: Optional[List[dict]] = None, context: Optional[str] = None) -> AsyncGenerator[dict, None]:
        """
        流式执行 ChatAgent，处理用户输入

        注意：历史消息的压缩现在由 Graph 的 history_manager_node 处理

        Args:
            user_input: 用户输入
            history: 历史消息列表（已压缩），格式: [{"role": "user/assistant", "content": "..."}]
            context: RAG检索的上下文信息（可选）

        Yields:
            结构化事件字典，包含 type 和相关数据：
            - {"type": "content", "content": "..."} - 文本内容
            - {"type": "thinking", "content": "..."} - 思考过程
            - {"type": "event", "data": {"title": "...", "status": "START/END/ERROR", "message": "..."}} - 工具调用事件
        """
        try:
            # 构建输入消息（context通过消息前缀注入）
            messages = self._build_messages(user_input, history, context)

            # 导入 Token 采集 Callback
            from app.callbacks import usage_metadata_callback

            # 流式执行 Agent（限制最大迭代轮数，防止死循环）
            async for event in self.agent_executor.astream_events(
                {"messages": messages},
                version="v2",
                config={
                    "recursion_limit": self.agent_max_iterations,
                    "callbacks": [usage_metadata_callback],
                }
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]

                    # 1. 提取 thinking 内容（qwen3 等思考模型的 reasoning_content）
                    reasoning = None
                    if hasattr(chunk, "additional_kwargs"):
                        reasoning = chunk.additional_kwargs.get("reasoning_content")
                    if reasoning:
                        yield {"type": "thinking", "content": reasoning}

                    # 2. 提取正常文本内容（跳过空内容和纯工具调用标签）
                    content = chunk.content if hasattr(chunk, "content") else ""
                    if content and content.strip() and not content.strip().startswith("<tool_call"):
                        yield {"type": "content", "content": content}

                elif kind == "on_chat_model_start":
                    # 模型开始思考
                    yield {"type": "thinking", "content": "正在思考..."}

                elif kind == "on_tool_start":
                    # 工具调用开始 → 发送 START 事件
                    tool_name = event.get("name", "unknown")
                    tool_input = ""
                    try:
                        tool_input = str(event.get("data", {}).get("input", ""))[:500]
                    except Exception:
                        pass
                    display_name = format_tool_display_name(tool_name)
                    yield {
                        "type": "event",
                        "data": {
                            "title": f"执行工具: {display_name}",
                            "status": "START",
                            "message": f"正在调用工具 {display_name}..." + (f"\n输入: {tool_input}" if tool_input else ""),
                            "tool_name": tool_name
                        }
                    }

                elif kind == "on_tool_end":
                    # 工具调用结束 → 发送 END 事件（携带返回内容）
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
                    yield {
                        "type": "event",
                        "data": {
                            "title": f"执行工具: {display_name}",
                            "status": "END",
                            "message": tool_output,
                            "tool_name": tool_name
                        }
                    }

        except Exception as e:
            logger.error(f"ChatAgent流式执行失败: {e}")
            yield {
                "type": "event",
                "data": {
                    "title": "执行出错",
                    "status": "ERROR",
                    "message": str(e)
                }
            }
            raise

