"""Researcher Agent - 信息检索专家"""
from app.core.agents.bases import BaseReactAgent
from app.tools import ResearcherTools


class ResearcherAgent(BaseReactAgent):
    """信息检索 Agent"""
    name = "researcher"
    prompt_name = "researcher"
    tools = ResearcherTools
    thinking_hint = "正在搜索信息..."
