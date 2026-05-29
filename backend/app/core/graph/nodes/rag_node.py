"""RAG 检索节点 - 自动检索用户知识库"""
from typing import List
from loguru import logger
from sqlmodel import select

from app.core.graph.state import ChatState
from app.database.session import get_session_ctx
from app.database.models import KnowledgeTable
from app.services.rag.handler import RagHandler


async def rag_node(state: ChatState) -> dict:
    """
    RAG 检索节点函数

    该节点自动从数据库中获取当前用户的知识库ID，然后执行 RAG 检索，
    将结果更新到 state 的 context 字段。

    Args:
        state: Graph 状态，包含 user_input

    Returns:
        更新后的状态字典，包含 context（检索结果）
    """
    try:
        user_input = state.get("user_input", "")

        logger.info(f"RAG 节点开始执行，查询: {user_input[:50]}...")

        # 1. 从数据库获取当前用户的知识库 ID
        from app.middleware.user_context import current_user_id
        user_id = str(current_user_id.get())
        async with get_session_ctx() as session:
            statement = select(KnowledgeTable.id).where(KnowledgeTable.user_id == user_id)
            result = await session.execute(statement)
            knowledge_ids: List[str] = [row for row in result.scalars().all()]

            if not knowledge_ids:
                logger.info("没有可用的知识库，跳过 RAG 检索")
                return {"rag_context": None}

            logger.info(f"找到 {len(knowledge_ids)} 个知识库: {knowledge_ids}")

            # 2. 执行 RAG 检索（在用户知识库中搜索，使用用户配置参数）
            context = await RagHandler.query(
                query=user_input,
                knowledge_ids=knowledge_ids
            )

            # 3. 处理检索结果
            if context and context != "未找到相关文档。":
                logger.info(f"RAG 节点检索成功，rag_context 长度: {len(context)}")
                return {"rag_context": context}
            else:
                logger.warning("RAG 节点未检索到相关文档，将使用纯对话模式")
                return {"rag_context": None}

    except Exception as e:
        logger.error(f"RAG 节点执行失败: {e}")
        # 即使失败也返回空 rag_context，避免中断整个流程
        return {"rag_context": None}
