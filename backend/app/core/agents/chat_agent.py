"""基于 LangChain 的聊天智能体实现"""
from typing import List, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from loguru import logger


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
        self.system_prompt = system_prompt or """你是一个智能助手Hubu Agent。

你的特点:
- 友好、专业、善于倾听
- 回答准确、简洁、有条理
- 支持多轮对话，能够记住对话历史中的关键信息（如用户名字、偏好等）
- 如果用户在之前的对话中提到过个人信息，你应该在后续对话中合理使用这些信息

注意事项:
- 对话历史已经在messages中提供，你可以根据历史内容进行回复
- 不要说"我无法保留对话历史"或"每次对话都是独立的"之类的话
- 如果用户问你记得什么，可以根据历史消息回答"""

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

    async def run(self, user_input: str, history: Optional[List[dict]] = None, context: Optional[str] = None) -> str:
        """
        执行 ChatAgent，处理用户输入

        注意：历史消息的压缩现在由 Graph 的 history_manager_node 处理

        Args:
            user_input: 用户输入
            history: 历史消息列表（已压缩），格式: [{"role": "user/assistant", "content": "..."}]
            context: RAG检索的上下文信息（可选）

        Returns:
            AI的回复
        """
        try:
            # 构建输入消息（context通过消息前缀注入）
            messages = self._build_messages(user_input, history, context)

            # 执行 Agent（限制最大迭代轮数，防止死循环）
            result = await self.agent_executor.ainvoke(
                {"messages": messages},
                config={"recursion_limit": self.agent_max_iterations}
            )
            response = result["messages"][-1].content

            logger.info(f"ChatAgent处理成功，回复长度: {len(response)}")
            return response

        except Exception as e:
            logger.error(f"ChatAgent执行失败: {e}")
            raise

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
            - {"type": "tool_start", "tool": "...", "input": "..."} - 工具调用开始
            - {"type": "tool_end", "tool": "...", "output": "..."} - 工具调用结束
        """
        try:
            # 构建输入消息（context通过消息前缀注入）
            messages = self._build_messages(user_input, history, context)

            # 流式执行 Agent（限制最大迭代轮数，防止死循环）
            async for event in self.agent_executor.astream_events(
                {"messages": messages},
                version="v2",
                config={"recursion_limit": self.agent_max_iterations}
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield {"type": "content", "content": content}

                elif kind == "on_chat_model_start":
                    # 模型开始思考
                    yield {"type": "thinking", "content": "正在思考..."}

                elif kind == "on_tool_start":
                    # 工具调用开始
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", "")
                    yield {"type": "tool_start", "tool": tool_name, "input": str(tool_input)}

                elif kind == "on_tool_end":
                    # 工具调用结束
                    tool_name = event.get("name", "unknown")
                    tool_output = ""
                    if hasattr(event.get("data", {}).get("output"), "content"):
                        tool_output = event["data"]["output"].content
                    else:
                        tool_output = str(event.get("data", {}).get("output", ""))
                    yield {"type": "tool_end", "tool": tool_name, "output": tool_output}

        except Exception as e:
            logger.error(f"ChatAgent流式执行失败: {e}")
            raise
