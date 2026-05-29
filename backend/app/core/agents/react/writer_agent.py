"""Skill Agent - 技能执行专家"""
from app.core.agents.bases import BaseReactAgent
from app.tools import SkillTools


class SkillAgent(BaseReactAgent):
    """技能执行 Agent"""
    name = "skill"
    prompt_name = "skill"
    tools = SkillTools
    thinking_hint = "正在执行技能..."
