"""综合处理节点 - 合并 RAG 检索结果与长期记忆，格式化输出"""
from loguru import logger

from app.config import settings
from app.core.graph.state import ChatState

NL = chr(10)  # 换行符常量，避免转义问题


async def merge_node(state: ChatState) -> dict:
    """
    综合处理节点

    将 rag_context 和 memory_context 进行合并和格式化，
    生成最终的 context 供 chat_agent 使用。

    不做去重——语义判断交给 LLM，避免误删有用信息。

    处理流程：
    1. 收集 rag_context 和 memory_context
    2. 格式化为统一结构（记忆优先）
    3. 长度控制（防止 context 过长，优先保留记忆）

    Args:
        state: Graph 状态，包含 rag_context 和 memory_context

    Returns:
        更新后的状态字典，包含合并后的 context
    """
    try:
        rag_context = state.get("rag_context")
        memory_context = state.get("memory_context")

        # 两者都为空，直接返回
        if not rag_context and not memory_context:
            logger.info("综合处理：rag_context 和 memory_context 均为空，无需合并")
            return {"context": None}

        # 只有 rag_context
        if rag_context and not memory_context:
            logger.info(f"综合处理：仅 rag_context，长度: {len(rag_context)}")
            return {"context": rag_context}

        # 只有 memory_context
        if memory_context and not rag_context:
            logger.info(f"综合处理：仅 memory_context，长度: {len(memory_context)}")
            return {"context": memory_context}

        # 两者都有，直接拼接
        logger.info(f"综合处理：合并 rag_context({len(rag_context)}) + memory_context({len(memory_context)})")

        # 记忆优先，知识库在后
        parts = []
        parts.append("【用户长期记忆】" + NL + memory_context)
        parts.append("【知识库检索结果】" + NL + rag_context)

        merged_context = (NL + NL).join(parts)

        # 长度控制：超过阈值时截断知识库部分，优先保留记忆
        MAX_CONTEXT_LENGTH = settings.MERGE_MAX_CONTEXT_LENGTH
        if len(merged_context) > MAX_CONTEXT_LENGTH:
            memory_part = "【用户长期记忆】" + NL + memory_context
            remaining = MAX_CONTEXT_LENGTH - len(memory_part) - 50  # 留分隔符空间
            if remaining > 200:
                truncated_rag = rag_context[:remaining]
                merged_context = (
                    memory_part + NL + NL
                    + "【知识库检索结果】" + NL
                    + truncated_rag + NL
                    + "...(内容已截断)"
                )
            else:
                merged_context = memory_part

            logger.info(f"综合处理：context 超长，截断至 {len(merged_context)} 字符")

        logger.info(f"综合处理完成：合并后 context 长度: {len(merged_context)}")
        return {"context": merged_context}

    except Exception as e:
        logger.error(f"综合处理节点执行失败: {e}")
        # 失败时降级：优先使用 rag_context，其次 memory_context
        fallback = state.get("rag_context") or state.get("memory_context")
        return {"context": fallback}
