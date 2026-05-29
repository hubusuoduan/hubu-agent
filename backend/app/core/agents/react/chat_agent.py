"""Chat Agent - 通用对话"""
from app.core.agents.bases import BaseReactAgent
from app.tools import ChatTools


class ChatAgent(BaseReactAgent):
    """通用对话 Agent（无工具，纯对话）"""
    name = "chat"
    prompt_name = "chat_agent"
    tools = ChatTools
    thinking_hint = "正在思考..."
