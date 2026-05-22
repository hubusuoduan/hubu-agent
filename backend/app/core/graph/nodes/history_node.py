"""对话历史管理节点"""
from typing import Optional
from loguru import logger
from langgraph.types import StreamWriter

from app.core.graph.state import ChatState
from app.core.agents.summary_agent import SummaryAgent
from app.utils.token_counter import TokenCounter
from app.services.llm_service import LLMService
from app.config import settings


# 全局 SummaryAgent 单例（无状态，无需按 session_id 缓存）
_summary_agent: Optional[SummaryAgent] = None


def get_summary_agent() -> SummaryAgent:
    """获取全局 SummaryAgent 实例（单例模式）"""
    global _summary_agent
    if _summary_agent is None:
        model = LLMService.get_model(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model_name=settings.LLM_MODEL
        )
        _summary_agent = SummaryAgent(model=model)
        logger.info("创建全局 SummaryAgent 实例")
    return _summary_agent


async def history_manager_node(state: ChatState) -> dict:
    """
    历史管理节点函数

    该节点负责：
    1. 从 state 中获取历史消息
    2. 智能压缩历史（使用 SummaryAgent 生成摘要）
    3. Token长度控制（动态截断）
    4. 将压缩后的历史更新到 state

    Args:
        state: Graph 状态，包含 messages, user_input 等

    Returns:
        更新后的状态字典，包含压缩后的 messages
    """
    try:
        messages = state.get("messages", [])
        session_id = state.get("session_id", "default")

        # 将 LangChain 消息转换为字典格式
        messages_dict = []
        for msg in messages:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "user" if msg.type == "human" else "assistant"
                if msg.type == "system":
                    role = "system"
                messages_dict.append({"role": role, "content": msg.content})

        # 如果消息数量较少，直接返回
        if len(messages_dict) <= settings.MAX_HISTORY_ROUNDS * 2:
            logger.info(f"历史消息数量 {len(messages_dict)} 未超过阈值，跳过压缩")
            return {"messages": messages}

        # 第一步：使用 SummaryAgent 生成摘要压缩
        compressed_dict = await _compress_with_summary(messages_dict)

        # 第二步：Token长度控制
        if settings.ENABLE_TOKEN_CONTROL:
            compressed_dict = await _control_token_length(compressed_dict)

        # 将字典转换回 LangChain 消息
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        compressed_messages = []
        for msg_dict in compressed_dict:
            role = msg_dict.get("role", "user")
            content = msg_dict.get("content", "")

            if role == "user":
                compressed_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                compressed_messages.append(AIMessage(content=content))
            elif role == "system":
                compressed_messages.append(SystemMessage(content=content))

        logger.info(f"历史管理完成: {len(messages)} -> {len(compressed_messages)} 条消息")
        return {"messages": compressed_messages}

    except Exception as e:
        logger.error(f"历史管理节点执行失败: {e}")
        # 失败时返回原始消息，避免中断流程
        return {"messages": state.get("messages", [])}


async def _compress_with_summary(messages_dict: list) -> list:
    """
    使用 SummaryAgent 压缩历史消息

    Args:
        messages_dict: 字典格式的消息列表

    Returns:
        压缩后的消息列表
    """
    # 获取全局 SummaryAgent
    summary_agent = get_summary_agent()

    # 分离旧消息和新消息
    max_messages = settings.MAX_HISTORY_ROUNDS * 2
    old_messages = messages_dict[:-max_messages]
    new_messages = messages_dict[-max_messages:]

    # 使用 SummaryAgent 生成摘要
    logger.info(f"触发历史摘要生成: 旧消息 {len(old_messages)} 条")
    summary = await summary_agent.summarize(old_messages)

    if summary:
        # 构建新的消息列表：摘要 + 最新对话
        summary_message = {"role": "user", "content": f"[历史对话摘要]\n{summary}\n\n请基于以上摘要和后续对话继续回答。"}
        compressed = [summary_message] + new_messages
        logger.info(f"摘要压缩成功: {len(messages_dict)} -> {len(compressed)} 条")
        return compressed
    else:
        # 摘要生成失败，使用简单裁剪
        logger.warning("摘要生成失败，降级为简单裁剪")
        return new_messages


async def _control_token_length(messages_dict: list) -> list:
    """
    控制消息列表的token长度

    Args:
        messages_dict: 字典格式的消息列表

    Returns:
        token控制后的消息列表
    """
    # 获取全局 SummaryAgent
    summary_agent = get_summary_agent()

    # 创建 TokenCounter，传入 SummaryAgent
    token_counter = TokenCounter(summary_agent=summary_agent)

    # 计算当前token数
    current_tokens = token_counter.count_message_tokens(messages_dict)
    max_tokens = settings.MAX_CONTEXT_TOKENS - settings.RESERVE_FOR_RESPONSE

    logger.info(f"当前上下文token: {current_tokens}, 限制: {max_tokens}")

    if current_tokens > max_tokens:
        # TokenCounter 内部会调用 SummaryAgent 生成二次摘要（不计算token占用）
        truncated = await token_counter.truncate_messages_by_tokens(
            messages_dict,
            max_tokens,
            preserve_first=True  # 保留第一条消息（原始摘要）
        )
        final_tokens = token_counter.count_message_tokens(truncated)
        logger.info(f"Token截断: {current_tokens} -> {final_tokens} tokens")
        return truncated
    else:
        logger.info("Token数在限制范围内，无需截断")
        return messages_dict
