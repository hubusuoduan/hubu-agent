"""Supervisor Agent - 意图路由"""
from typing import List, Optional
from loguru import logger

from app.core.agents.bases import BaseLLMAgent
from app.core.graph.state import ChatState
from app.services.settings_service import SettingsFactory
from app.prompts import load_prompt

# 系统 Agent 名称（固定）
SYSTEM_AGENTS = {"chat", "researcher", "coder", "skill"}


def _build_agent_descriptions(user_agents_desc: list = None) -> str:
    """动态构建 Agent 描述文本，替换 supervisor.md 中的 {{agent_descriptions}}

    Args:
        user_agents_desc: 用户自建 Agent 描述列表，格式:
            [{"name": "user_translator", "display_name": "翻译官", "description": "擅长中英互译"}]

    Returns:
        完整的 Agent 描述 Markdown 文本
    """
    parts = []

    # 系统 Agent 描述（固定）
    system_agent_desc = [
        ("chat", "通用对话 Agent", "闲聊、简单问答、不需要工具的对话"),
        ("researcher", "信息检索 Agent", "搜索网络信息、抓取网页、查询知识库、获取天气"),
        ("coder", "代码执行 Agent", "运行代码、数据处理、计算、安装依赖包"),
        ("skill", "技能执行 Agent", "使用 Skill 系统生成/编辑文档、执行 Skill 脚本、创建 Word/PDF/PPT/Excel 等文件"),
    ]

    for i, (name, title, suitable) in enumerate(system_agent_desc, 1):
        parts.append(f"{i}. **{name}** — {title}")
        parts.append(f"   - 适合：{suitable}")

    # 用户自建 Agent 描述（动态）
    if user_agents_desc:
        for i, ua in enumerate(user_agents_desc, len(system_agent_desc) + 1):
            name = ua.get("name", "")
            display_name = ua.get("display_name", name)
            description = ua.get("description", "")
            parts.append(f"{i}. **{name}** — {display_name}")
            if description:
                parts.append(f"   - 适合：{description}")

    return "\n".join(parts)


class SupervisorAgent(BaseLLMAgent):
    """Supervisor Agent - 意图路由

    分析用户输入和当前状态，返回路由决策。
    继承 BaseLLMAgent（单次 LLM 调用）。
    """

    name = "supervisor"
    prompt_name = "supervisor"

    @classmethod
    async def _build_user_prompt(cls, state: ChatState) -> str:
        """构建用户提示词"""
        user_input = state.get("user_input", "")
        review_feedback = state.get("review_feedback", "")
        retry_count = state.get("retry_count", 0)
        agent_scratchpad = state.get("agent_scratchpad", [])

        context_parts = [f"用户输入: {user_input}"]

        if agent_scratchpad:
            from app.utils.text import format_scratchpad
            context_parts.append("已执行的 Agent 记录:\n" + format_scratchpad(agent_scratchpad, max_output=500))

        if review_feedback:
            context_parts.append(f"审查反馈: {review_feedback}")

        reviewer_max_retries = SettingsFactory.get(key="REVIEWER_MAX_RETRIES")
        context_parts.append(f"当前重试次数: {retry_count}/{reviewer_max_retries}")

        return "\n\n".join(context_parts)

    @classmethod
    def _build_system_prompt(cls, user_agents_desc: list = None) -> str:
        """动态构建 system_prompt，将 Agent 描述注入模板

        Args:
            user_agents_desc: 用户自建 Agent 描述列表

        Returns:
            替换后的完整 system_prompt
        """
        template = load_prompt("supervisor")
        agent_descriptions = _build_agent_descriptions(user_agents_desc)
        return template.replace("{{agent_descriptions}}", agent_descriptions)

    @classmethod
    async def route(cls, state: ChatState, user_agents_desc: list = None) -> str:
        """执行路由决策（纯 LLM 调用）

        Args:
            state: Graph 状态
            user_agents_desc: 用户自建 Agent 描述列表，格式:
                [{"name": "user_translator", "display_name": "翻译官", "description": "..."}]

        Returns:
            Agent 名称字符串，或 None（调用失败）
        """
        try:
            # 动态构建 system_prompt（注入用户 Agent 描述）
            system_prompt = cls._build_system_prompt(user_agents_desc)
            user_prompt = await cls._build_user_prompt(state)
            response_text = await cls.invoke_llm(user_prompt, system_prompt=system_prompt)

            next_agent = response_text.lower().strip()
            logger.info(f"Supervisor LLM 返回: {next_agent}")
            return next_agent

        except Exception as e:
            logger.error(f"Supervisor Agent 执行失败: {e}")
            return None
