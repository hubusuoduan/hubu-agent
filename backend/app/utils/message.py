"""LangChain 消息转换工具

消除 history_node、chat.py、summary_agent、base_react_agent 中
重复的消息格式转换逻辑。
"""
from typing import List, Dict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def lc_messages_to_dicts(messages: list) -> List[Dict]:
    """将 LangChain 消息列表转换为字典列表

    LangChain 消息的 type 字段: "human" / "ai" / "system"
    字典的 role 字段: "user" / "assistant" / "system"

    Args:
        messages: LangChain 消息列表

    Returns:
        字典列表，格式: [{"role": "user", "content": "..."}, ...]
    """
    result = []
    for msg in messages:
        if hasattr(msg, 'type') and hasattr(msg, 'content'):
            role = "user" if msg.type == "human" else "assistant"
            if msg.type == "system":
                role = "system"
            result.append({"role": role, "content": msg.content})
    return result


def dicts_to_lc_messages(messages: List[Dict]) -> list:
    """将字典列表转换为 LangChain 消息列表

    Args:
        messages: 字典列表，格式: [{"role": "user", "content": "..."}, ...]

    Returns:
        LangChain 消息列表
    """
    result = []
    for msg_dict in messages:
        role = msg_dict.get("role", "user")
        content = msg_dict.get("content", "")
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))
    return result


def format_messages_text(messages: list) -> str:
    """将消息列表格式化为纯文本（用于摘要生成等场景）

    同时支持 LangChain 消息对象和字典格式。

    Args:
        messages: 消息列表（LangChain 消息或字典）

    Returns:
        格式化后的文本，如: "用户: 你好\n\n助手: 你好！"
    """
    lines = []
    for msg in messages:
        if hasattr(msg, "type") and hasattr(msg, "content"):
            if msg.type == "human":
                lines.append(f"用户: {msg.content}")
            elif msg.type == "ai":
                lines.append(f"助手: {msg.content}")
        elif isinstance(msg, dict):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"助手: {content}")
    return "\n\n".join(lines)
