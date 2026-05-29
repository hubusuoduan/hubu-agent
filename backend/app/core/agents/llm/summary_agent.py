"""对话历史摘要 Agent - 专门负责生成对话历史摘要"""
from loguru import logger

from app.core.agents.bases import BaseLLMAgent
from app.core.graph.state import ChatState


class SummaryAgent(BaseLLMAgent):
    """对话历史摘要 Agent

    专门用于生成对话历史的摘要，帮助压缩上下文并保留关键信息。
    继承 BaseLLMAgent（单次 LLM 调用）。
    """

    name = "summary"
    prompt_name = "summary_agent"

    @classmethod
    def _build_user_prompt(cls, state: ChatState) -> str:
        """构建用户提示词"""
        messages = state.get("messages", [])
        conversation_text = cls._format_messages(messages)
        return f"""请对以下对话历史生成摘要：

{conversation_text}

请按照要求的格式输出摘要。"""

    @classmethod
    def _format_messages(cls, messages: list) -> str:
        """将消息列表格式化为文本"""
        from app.utils.message import format_messages_text
        return format_messages_text(messages)

    @classmethod
    async def summarize(cls, state: ChatState) -> str:
        """生成对话历史摘要（纯 LLM 调用）

        Args:
            state: Graph 状态

        Returns:
            摘要文本，失败返回空字符串
        """
        try:
            user_prompt = cls._build_user_prompt(state)
            summary = await cls.invoke_llm(user_prompt)
            logger.info(f"摘要生成成功，长度: {len(summary)}")
            return summary

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return ""
