"""对话历史摘要 Agent - 专门负责生成对话历史摘要"""
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from app.prompts import load_prompt


class SummaryAgent:
    """对话历史摘要 Agent

    专门用于生成对话历史的摘要，帮助压缩上下文并保留关键信息。
    """

    def __init__(self, model: ChatOpenAI):
        """
        初始化摘要 Agent

        Args:
            model: LLM模型实例
        """
        self.model = model
        self.system_prompt = load_prompt("summary_agent")

    async def summarize(self, messages: List[Dict]) -> Optional[str]:
        """
        生成对话历史摘要

        Args:
            messages: 对话历史消息列表，格式: [{"role": "user/assistant", "content": "..."}]

        Returns:
            摘要文本，如果失败则返回None
        """
        try:
            # 将消息格式化为文本
            conversation_text = self._format_messages(messages)

            # 构建用户提示词
            user_prompt = f"""请对以下对话历史生成摘要：

{conversation_text}

请按照要求的格式输出摘要。"""

            # 调用模型生成摘要，注入 Token 采集 Callback
            from app.callbacks import usage_metadata_callback
            response = await self.model.ainvoke(
                [SystemMessage(content=self.system_prompt),
                 HumanMessage(content=user_prompt)],
                config={"callbacks": [usage_metadata_callback]}
            )

            summary = response.content
            logger.info(f"摘要 Agent 生成成功，摘要长度: {len(summary)}")

            return summary

        except Exception as e:
            logger.error(f"摘要 Agent 执行失败: {e}")
            return None

    def _format_messages(self, messages: List[Dict]) -> str:
        """
        将消息列表格式化为文本

        Args:
            messages: 消息列表

        Returns:
            格式化后的文本
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"助手: {content}")

        return "\n\n".join(lines)
