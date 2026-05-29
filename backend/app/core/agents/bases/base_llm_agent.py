"""LLM Agent 基类 - 封装单次 LLM 调用的公共逻辑"""
from typing import Optional
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_service import LLMService
from app.prompts import load_prompt
from app.callbacks import usage_metadata_callback


class BaseLLMAgent:
    """LLM Agent 基类

    封装单次 LLM 调用的公共逻辑：
    - prompt 加载
    - LLM 调用
    - 结果解析

    适用于非 ReAct 模式的 Agent，如：
    - Supervisor（路由决策）
    - Reviewer（审查决策）
    - SummaryAgent（摘要生成）

    子类只需定义：
    - name: Agent 名称
    - prompt_name: prompt 文件名
    - parse_response(response_text): 解析 LLM 回复的子类逻辑
    """

    name: str = "base_llm"
    prompt_name: str = "chat_agent"

    @classmethod
    def load_system_prompt(cls) -> str:
        """加载系统提示词"""
        return load_prompt(cls.prompt_name)

    @classmethod
    async def invoke_llm(
        cls,
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """调用 LLM 并返回原始回复文本

        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词（默认从 prompt 文件加载）

        Returns:
            LLM 回复的原始文本
        """
        if system_prompt is None:
            system_prompt = cls.load_system_prompt()

        model = await LLMService.get_model_async()
        response = await model.ainvoke(
            [SystemMessage(content=system_prompt),
             HumanMessage(content=user_prompt)],
            config={"callbacks": [usage_metadata_callback]}
        )
        return response.content.strip()


