"""Reviewer Agent - 审查回复质量"""
from loguru import logger

from app.core.agents.bases import BaseLLMAgent
from app.core.graph.state import ChatState
from app.utils.text import parse_json


class ReviewerAgent(BaseLLMAgent):
    """Reviewer Agent - 审查回复并决定下一步

    审查 Agent 的回复，结合任务计划判断：推进/通过/重试。
    继承 BaseLLMAgent（单次 LLM 调用）。
    """

    name = "reviewer"
    prompt_name = "reviewer"

    @classmethod
    def _build_user_prompt(cls, state: ChatState) -> str:
        """构建用户提示词"""
        from app.utils.text import truncate, format_scratchpad

        user_input = state.get("user_input", "")
        response = state.get("response", "")
        agent_scratchpad = state.get("agent_scratchpad", [])
        task_plan = state.get("task_plan", [])
        plan_index = state.get("plan_index", 0)

        # 构建任务计划信息
        plan_info = ""
        if task_plan:
            steps = []
            for i, step in enumerate(task_plan):
                agent_name = step.get("agent", "?") if isinstance(step, dict) else str(step)
                task_desc = step.get("task", "") if isinstance(step, dict) else ""
                label = f"{agent_name}: {task_desc}" if task_desc else agent_name
                if i < plan_index:
                    steps.append(f"  {i + 1}. ~~{label}~~ (已完成)")
                elif i == plan_index:
                    steps.append(f"  {i + 1}. **{label}** (当前步骤)")
                else:
                    steps.append(f"  {i + 1}. {label} (待执行)")
            plan_info = "\n\n任务计划:\n" + "\n".join(steps)

        scratch_summary = ""
        if agent_scratchpad:
            scratch_summary = "\n\n已执行的 Agent 记录:\n" + format_scratchpad(agent_scratchpad, max_output=800)

        return f"""请审查以下回复并结合任务计划决定下一步：

用户输入: {user_input}
{plan_info}

当前 Agent 回复: {truncate(response, 2000)}{scratch_summary}

请返回 JSON 格式的审查结果。"""

    @classmethod
    async def review(cls, state: ChatState) -> dict:
        """执行审查（纯 LLM 调用 + 解析）

        Args:
            state: Graph 状态

        Returns:
            {"result": "pass"|"advance"|"retry", "feedback": "..."} 或 None（解析失败）
        """
        try:
            user_prompt = cls._build_user_prompt(state)
            response_text = await cls.invoke_llm(user_prompt)

            # 解析结果
            result = parse_json(response_text)

            if result is None:
                logger.warning(f"Reviewer JSON 解析失败: {response_text[:100]}")
                return None

            review_result = result.get("result", "pass").strip().lower()
            review_feedback = result.get("feedback", "").strip()

            # 验证结果合法性
            if review_result not in ("pass", "advance", "retry"):
                review_result = "pass"

            logger.info(f"Reviewer 审查结果: {review_result}, 反馈: {review_feedback[:100]}")

            return {
                "result": review_result,
                "feedback": review_feedback,
            }

        except Exception as e:
            logger.error(f"Reviewer Agent 执行失败: {e}")
            return None
