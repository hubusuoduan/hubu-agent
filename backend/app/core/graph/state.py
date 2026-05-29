"""Graph State 定义"""
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from operator import add


def _append_list(existing: list, new: list) -> list:
    """列表追加合并函数，用于 agent_scratchpad 的 reducer"""
    if existing is None:
        existing = []
    if new is None:
        new = []
    return existing + new


class ChatState(TypedDict):
    """聊天 Graph 的状态定义

    Attributes:
        messages: 消息列表，使用 add_messages 注解实现消息追加
        user_input: 用户当前输入
        rag_context: RAG 检索的上下文信息（由 rag 节点写入）
        memory_context: 长期记忆的上下文信息（由 memory 节点写入）
        context: 综合处理后的最终上下文（由 merge 节点写入，供各 Agent 使用）
        session_id: 会话ID
        user_id: 用户ID
        response: AI 的最终回复
        next_agent: Supervisor 路由决策，决定下一个执行的 Agent
        task_plan: Supervisor 制定的任务计划，格式: [{"agent": "researcher", "task": "搜索信息"}, ...]
        plan_index: 当前执行到任务计划的第几步（从 0 开始）
        task_instruction: 当前步骤的任务指令（Supervisor 为当前 Agent 生成的具体说明）
        review_result: Reviewer 审查结果 ("pass" / "retry" / "advance")
        review_feedback: Reviewer 审查反馈（不够时说明缺什么）
        retry_count: 当前重试次数（防止死循环）
        agent_scratchpad: 各 Agent 的执行记录列表，格式: [{"agent": "researcher", "output": "..."}]
        user_agents_desc: 用户自建 Agent 描述列表，格式: [{"name": "user_translator", "display_name": "翻译官", "description": "..."}]
    """
    messages: Annotated[list, add_messages]
    user_input: str
    rag_context: Optional[str]
    memory_context: Optional[str]
    context: Optional[str]
    session_id: str
    user_id: str
    response: str
    next_agent: str
    task_plan: list
    plan_index: int
    task_instruction: str
    review_result: str
    review_feedback: str
    retry_count: int
    agent_scratchpad: Annotated[list, _append_list]
    user_agents_desc: list

