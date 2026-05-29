"""对话历史管理节点"""
from loguru import logger

from app.core.graph.state import ChatState
from app.core.agents.llm import SummaryAgent
from app.utils.token_counter import TokenCounter
from app.utils.message import lc_messages_to_dicts, dicts_to_lc_messages
from app.services.settings_service import SettingsFactory


async def history_manager_node(state: ChatState) -> dict:
    """历史管理节点函数

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

        # 将 LangChain 消息转换为字典格式
        messages_dict = lc_messages_to_dicts(messages)

        # 如果消息数量较少，直接返回
        max_history_rounds = SettingsFactory.get(key="MAX_HISTORY_ROUNDS")
        if len(messages_dict) <= max_history_rounds * 2:
            logger.info(f"历史消息数量 {len(messages_dict)} 未超过阈值，跳过压缩")
            return {"messages": messages}

        # 第一步：使用 SummaryAgent 生成摘要压缩
        compressed_dict = await _compress_with_summary(state, messages_dict)

        # 第二步：Token长度控制
        enable_token_control = SettingsFactory.get(key="ENABLE_TOKEN_CONTROL")
        if enable_token_control:
            compressed_dict = await _control_token_length(state, compressed_dict)

        # 将字典转换回 LangChain 消息
        compressed_messages = dicts_to_lc_messages(compressed_dict)

        logger.info(f"历史管理完成: {len(messages)} -> {len(compressed_messages)} 条消息")
        return {"messages": compressed_messages}

    except Exception as e:
        logger.error(f"历史管理节点执行失败: {e}")
        # 失败时返回原始消息，避免中断流程
        return {"messages": state.get("messages", [])}


async def _compress_with_summary(state: ChatState, messages_dict: list) -> list:
    """使用 SummaryAgent 压缩历史消息

    Args:
        state: Graph 状态（供 SummaryAgent 构建提示词）
        messages_dict: 字典格式的消息列表

    Returns:
        压缩后的消息列表
    """
    # 分离旧消息和新消息
    max_history_rounds = SettingsFactory.get(key="MAX_HISTORY_ROUNDS")
    max_messages = max_history_rounds * 2
    old_messages = messages_dict[:-max_messages]
    new_messages = messages_dict[-max_messages:]

    # 构建临时 state 供 SummaryAgent 使用
    summary_state = dict(state)
    summary_state["messages"] = old_messages

    # 使用 SummaryAgent 生成摘要
    logger.info(f"触发历史摘要生成: 旧消息 {len(old_messages)} 条")
    summary = await SummaryAgent.summarize(summary_state)

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


async def _control_token_length(state: ChatState, messages_dict: list) -> list:
    """控制消息列表的token长度

    Args:
        state: Graph 状态（供 SummaryAgent 构建提示词）
        messages_dict: 字典格式的消息列表

    Returns:
        token控制后的消息列表
    """
    # 创建 TokenCounter，传入 state 供二次摘要使用
    token_counter = TokenCounter(state=state)

    # 计算当前token数
    current_tokens = token_counter.count_message_tokens(messages_dict)
    max_context_tokens = SettingsFactory.get(key="MAX_CONTEXT_TOKENS")
    reserve_for_response = SettingsFactory.get(key="RESERVE_FOR_RESPONSE")
    max_tokens = max_context_tokens - reserve_for_response

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
