"""RAG 检索节点 - 自动检索所有知识库"""
from typing import List
from loguru import logger
from sqlmodel import select

from app.core.graph.state import ChatState
from app.database.session import get_async_session
from app.database.models import KnowledgeTable
from app.services.rag.handler import RagHandler


async def rag_node(state: ChatState) -> dict:
    """
    RAG 检索节点函数
    
    该节点自动从数据库中获取所有知识库ID，然后执行 RAG 检索，
    将结果更新到 state 的 context 字段。
    
    Args:
        state: Graph 状态，包含 user_input
        
    Returns:
        更新后的状态字典，包含 context（检索结果）
    """
    try:
        user_input = state.get("user_input", "")
        
        logger.info(f"RAG 节点开始执行，查询: {user_input[:50]}...")
        
        # 1. 从数据库获取所有知识库 ID
        async for session in get_async_session():
            try:
                statement = select(KnowledgeTable.id)
                result = await session.execute(statement)
                knowledge_ids: List[str] = [row for row in result.scalars().all()]
                
                if not knowledge_ids:
                    logger.info("没有可用的知识库，跳过 RAG 检索")
                    return {"context": None}
                
                logger.info(f"找到 {len(knowledge_ids)} 个知识库: {knowledge_ids}")
                
                # 2. 执行 RAG 检索（自动在所有知识库中搜索）
                context = await RagHandler.query(
                    query=user_input,
                    knowledge_ids=knowledge_ids,
                    top_k=5,
                    min_score=0.3
                )
                
                # 3. 处理检索结果
                if context and context != "未找到相关文档。":
                    logger.info(f"RAG 节点检索成功，context 长度: {len(context)}")
                    return {"context": context}
                else:
                    logger.info("RAG 节点未检索到相关文档")
                    return {"context": None}
                    
            finally:
                await session.close()
                break  # 只需要一次会话
        
    except Exception as e:
        logger.error(f"RAG 节点执行失败: {e}")
        # 即使失败也返回空 context，避免中断整个流程
        return {"context": None}
