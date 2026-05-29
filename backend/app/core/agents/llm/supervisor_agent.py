"""Supervisor Agent - 任务规划"""
from typing import List, Optional
from loguru import logger

from app.core.agents.bases import BaseLLMAgent
from app.core.graph.state import ChatState
from app.services.settings_service import SettingsFactory
from app.prompts import load_prompt
from app.utils.text import parse_json

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
    """Supervisor Agent - 任务规划

    分析用户输入和当前状态，制定任务执行计划。
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
        task_plan = state.get("task_plan", [])
        plan_index = state.get("plan_index", 0)

        context_parts = [f"用户输入: {user_input}"]

        if task_plan:
            context_parts.append(f"当前任务计划: {task_plan}")
            context_parts.append(f"已执行到第 {plan_index} 步")

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
    async def plan(cls, state: ChatState, user_agents_desc: list = None) -> Optional[List[dict]]:
        """制定任务执行计划（纯 LLM 调用）

        Args:
            state: Graph 状态
            user_agents_desc: 用户自建 Agent 描述列表，格式:
                [{"name": "user_translator", "display_name": "翻译官", "description": "..."}]

        Returns:
            任务计划列表，如 [{"agent": "researcher", "task": "搜索信息"}, ...]，或 None（调用失败）
        """
        try:
            # 动态构建 system_prompt（注入用户 Agent 描述）
            system_prompt = cls._build_system_prompt(user_agents_desc)
            user_prompt = await cls._build_user_prompt(state)
            response_text = await cls.invoke_llm(user_prompt, system_prompt=system_prompt)

            logger.info(f"Supervisor LLM 返回: {response_text[:200]}")

            # 解析 JSON 格式的任务计划
            result = parse_json(response_text)
            if result and isinstance(result.get("plan"), list):
                plan = []
                for item in result["plan"]:
                    if isinstance(item, dict) and item.get("agent"):
                        plan.append({
                            "agent": str(item["agent"]).strip().lower(),
                            "task": str(item.get("task", "")).strip(),
                        })
                    elif isinstance(item, str) and item.strip():
                        # 兼容旧格式：纯字符串
                        plan.append({"agent": item.strip().lower(), "task": ""})
                if plan:
                    logger.info(f"Supervisor 任务计划: {plan}")
                    return plan

            # JSON 解析失败，尝试从文本中提取 Agent 名称
            logger.warning(f"Supervisor JSON 解析失败，尝试从文本提取: {response_text[:100]}")
            plan = []
            for word in response_text.lower().split():
                word = word.strip("[]\"'")
                if word in SYSTEM_AGENTS or word.startswith("user_"):
                    plan.append({"agent": word, "task": ""})
            if plan:
                logger.info(f"Supervisor 从文本提取计划: {plan}")
                return plan

            logger.warning("Supervisor 未能生成有效计划")
            return None

        except Exception as e:
            logger.error(f"Supervisor Agent 执行失败: {e}")
            return None
