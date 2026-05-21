"""RAG核心处理器"""
from typing import List, Optional
from loguru import logger

from app.config import settings
from app.services.rag.embedding import get_embedding
from app.services.rag.vector_store import vector_store
from app.services.rag.reranker import reranker, RerankedDocument
from app.utils.doc_parser import SimpleDocParser


class RagHandler:
    """RAG处理器"""
    
    @classmethod
    async def index_documents(cls, knowledge_id: str, file_id: str, file_name: str, file_path: Optional[str] = None, content: Optional[str] = None) -> List[str]:
        """
        索引文档到向量存储
        
        Args:
            knowledge_id: 知识库ID
            file_id: 文件ID
            file_name: 文件名
            file_path: 文件路径（可选）
            content: 直接传入的文本内容（可选）
            
        Returns:
            文档chunk ID列表
        """
        # 1. 解析文档或处理直接传入的内容
        if content:
            chunks = SimpleDocParser.parse_content(content)
        elif file_path:
            chunks = SimpleDocParser.parse_file(file_path)
        else:
            logger.warning("必须提供 file_path 或 content")
            return []
            
        if not chunks:
            logger.warning(f"文档解析失败: {file_path or 'content'}")
            return []
        
        # 2. 为每个chunk生成向量并存储
        chunk_ids = []
        chunk_data_list = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            
            # 准备chunk数据
            chunk_data = {
                "chunk_id": chunk_id,
                "content": chunk,
                "file_id": file_id,
                "file_name": file_name,
                "knowledge_id": knowledge_id
            }
            chunk_data_list.append(chunk_data)
        
        # 3. 批量插入到Milvus
        success = await vector_store.add_documents(knowledge_id, chunk_data_list)
        
        if success:
            logger.info(f"成功索引 {len(chunk_ids)} 个文档块到知识库 {knowledge_id}")
            return chunk_ids
        else:
            logger.error(f"索引文档块失败")
            return []
    
    @classmethod
    async def query(cls, query: str, knowledge_ids: List[str], top_k: int = None, min_score: float = None) -> str:
        """
        RAG查询
        
        Args:
            query: 查询文本
            knowledge_ids: 知识库ID列表
            top_k: 每个知识库返回结果数量(默认从配置读取)
            min_score: 最小分数阈值(默认从配置读取)
            
        Returns:
            检索到的相关文档内容
        """
        # 使用配置中的默认值
        if top_k is None:
            top_k = settings.RAG_TOP_K
        if min_score is None:
            min_score = settings.RAG_MIN_SCORE
            
        logger.info(f"开始RAG查询: query长度={len(query)}, 知识库数量={len(knowledge_ids)}, top_k={top_k}, min_score={min_score}")
        
        # 1. 获取查询向量
        query_embedding = await get_embedding(query)
        logger.debug(f"查询向量维度: {len(query_embedding)}")
        
        # 2. 从每个知识库检索文档
        all_documents = []
        for knowledge_id in knowledge_ids:
            docs = await vector_store.search(query_embedding, knowledge_id, top_k=top_k)
            logger.debug(f"知识库 {knowledge_id} 检索到 {len(docs)} 个文档")
            all_documents.extend(docs)
        
        logger.info(f"总计检索到 {len(all_documents)} 个文档(未去重)")
        
        # 3. 按分数排序并去重
        all_documents.sort(key=lambda x: x.get("score", 0), reverse=True)
        seen_chunk_ids = set()
        unique_docs = []
        for doc in all_documents:
            chunk_id = doc.get("chunk_id")
            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                unique_docs.append(doc)
        
        logger.info(f"去重后剩余 {len(unique_docs)} 个唯一文档")
        
        # 4. 重排序(传入元数据)
        reranker_top_n = settings.RAG_RERANKER_TOP_N
        doc_contents = [doc.get("content", "") for doc in unique_docs[:reranker_top_n]]  # 从配置读取重排序数量
        doc_metadata = [{"chunk_id": doc.get("chunk_id"), "file_name": doc.get("file_name")} for doc in unique_docs[:reranker_top_n]]
        
        if not doc_contents:
            logger.warning("未检索到任何文档")
            return "未找到相关文档。"
        
        reranked_docs = await reranker.rerank_documents(query, doc_contents, doc_metadata)
        
        # 5. 过滤低分数结果并拼接
        filtered_results = [doc for doc in reranked_docs if doc.score >= min_score]
        
        if not filtered_results:
            logger.warning(f"所有文档分数低于阈值 {min_score}")
            return "未找到相关文档。"
        
        final_result = "\n\n".join(result.content for result in filtered_results)
        
        # 记录检索效果
        logger.info(f"RAG查询完成: "
                   f"检索={len(all_documents)}, "
                   f"去重={len(unique_docs)}, "
                   f"重排序后={len(reranked_docs)}, "
                   f"过滤后={len(filtered_results)}, "
                   f"最终长度={len(final_result)}")
        
        return final_result
    
    @classmethod
    async def delete_documents(cls, file_id: str, knowledge_id: str):
        """
        删除文档
        
        Args:
            file_id: 文件ID
            knowledge_id: 知识库ID
        """
        await vector_store.delete_by_file_id(file_id, knowledge_id)
        logger.info(f"删除文件 {file_id} 在知识库 {knowledge_id} 中的文档")
