"""Coder Agent - 代码执行专家"""
from app.core.agents.bases import BaseReactAgent
from app.tools import CoderTools


class CoderAgent(BaseReactAgent):
    """代码执行 Agent"""
    name = "coder"
    prompt_name = "coder"
    tools = CoderTools
    thinking_hint = "正在编写代码..."
