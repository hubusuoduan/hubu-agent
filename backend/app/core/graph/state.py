"""Graph State 定义"""
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    """聊天 Graph 的状态定义
    
    Attributes:
        messages: 消息列表，使用 add_messages 注解实现消息追加
        user_input: 用户当前输入
        context: RAG 检索的上下文信息（可选）
        session_id: 会话ID
        response: AI 的最终回复
    """
    messages: Annotated[list, add_messages]
    user_input: str
    context: Optional[str]
    session_id: str
    user_id: str
    response: str
