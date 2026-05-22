"""聊天 Agent 节点"""
from typing import Dict
from loguru import logger
from langgraph.types import StreamWriter

from app.core.graph.state import ChatState
from app.core.agents.chat_agent import ChatAgent
from app.config import settings
from app.services.llm_service import LLMService
from app.tools import AgentTools


# 全局 ChatAgent 实例缓存
_agent_cache: Dict[str, ChatAgent] = {}


def get_or_create_agent(session_id: str) -> ChatAgent:
    """
    获取或创建 ChatAgent 实例
    
    Args:
        session_id: 会话ID
        
    Returns:
        ChatAgent 实例
    """
    if session_id not in _agent_cache:
        model = LLMService.get_model(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model_name=settings.LLM_MODEL
        )
        _agent_cache[session_id] = ChatAgent(model=model, tools=AgentTools)
        logger.info(f"创建新ChatAgent实例: {session_id}")
    
    return _agent_cache[session_id]


async def chat_agent_node(state: ChatState) -> dict:
    """
    聊天 Agent 节点函数
    
    该节点从 state 中获取用户输入、上下文和历史消息，
    调用 ChatAgent 进行处理，并将结果更新到 state 中。
    
    Args:
        state: Graph 状态，包含 messages, user_input, context 等
        
    Returns:
        更新后的状态字典，包含 response
    """
    try:
        # 从 state 中提取信息
        user_input = state.get("user_input", "")
        context = state.get("context")
        messages = state.get("messages", [])
        
        # 将 LangChain 消息格式转换为历史消息格式
        history = []
        for msg in messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "user" if msg.type == "human" else "assistant"
                history.append({"role": role, "content": msg.content})
        
        # 获取或创建 ChatAgent 实例
        agent = get_or_create_agent(state.get("session_id", "default"))
        
        # 执行 ChatAgent
        response = await agent.run(
            user_input=user_input,
            history=history if history else None,
            context=context
        )
        
        logger.info(f"ChatAgent 节点执行成功，回复长度: {len(response)}")
        
        # 返回更新的状态
        return {
            "response": response
        }
        
    except Exception as e:
        logger.error(f"ChatAgent 节点执行失败: {e}")
        raise


async def stream_chat_agent_node(state: dict, writer: StreamWriter) -> dict:
    """
    流式聊天 Agent 节点函数
    
    该节点从 state 中获取用户输入、上下文和历史消息，
    调用 ChatAgent 进行流式处理，并通过 StreamWriter 发送数据。
    
    Args:
        state: Graph 状态，包含 messages, user_input, context 等
        writer: LangGraph 的 StreamWriter，用于发送自定义数据
        
    Returns:
        更新后的状态字典
    """
    try:
        # 从 state 中提取信息
        user_input = state.get("user_input", "")
        context = state.get("context")
        messages = state.get("messages", [])
        
        # 将 LangChain 消息格式转换为历史消息格式
        history = []
        for msg in messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "user" if msg.type == "human" else "assistant"
                history.append({"role": role, "content": msg.content})
        
        # 获取或创建 ChatAgent 实例
        agent = get_or_create_agent(state.get("session_id", "default"))
        
        # 流式执行 ChatAgent，并通过 writer 发送数据
        full_response = ""
        async for chunk in agent.stream_run(
            user_input=user_input,
            history=history if history else None,
            context=context
        ):
            if chunk:
                full_response += chunk
                # 使用 writer 发送自定义数据
                writer(chunk)
        
        logger.info(f"流式 ChatAgent 节点执行完成，回复长度: {len(full_response)}")
        
        # 返回完整的 response，供后续节点（如 memory_extract）使用
        return {"response": full_response}
        
    except Exception as e:
        logger.error(f"流式 ChatAgent 节点执行失败: {e}")
        raise
