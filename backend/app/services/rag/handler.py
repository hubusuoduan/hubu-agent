"""RAG核心处理器"""
from typing import List, Optional
from loguru import logger

from app.services.rag.embedding import get_embedding
from app.services.rag.vector_store import vector_store
from app.services.rag.reranker import reranker, RerankedDocument
from app.services.rag.doc_parser import SimpleDocParser


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
    async def query(cls, query: str, knowledge_ids: List[str], top_k: int = 5, min_score: float = 0.3) -> str:
        """
        RAG查询
        
        Args:
            query: 查询文本
            knowledge_ids: 知识库ID列表
            top_k: 返回结果数量
            min_score: 最小分数阈值
            
        Returns:
            检索到的相关文档内容
        """
        # 1. 获取查询向量
        query_embedding = await get_embedding(query)
        
        # 2. 从每个知识库检索文档
        all_documents = []
        for knowledge_id in knowledge_ids:
            docs = await vector_store.search(query_embedding, knowledge_id, top_k=top_k)
            all_documents.extend(docs)
        
        # 3. 按分数排序并去重
        all_documents.sort(key=lambda x: x.get("score", 0), reverse=True)
        seen_chunk_ids = set()
        unique_docs = []
        for doc in all_documents:
            chunk_id = doc.get("chunk_id")
            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                unique_docs.append(doc)
        
        # 4. 重排序
        doc_contents = [doc.get("content", "") for doc in unique_docs[:10]]  # 最多取10个文档进行重排序
        if not doc_contents:
            return "未找到相关文档。"
        
        reranked_docs = await reranker.rerank_documents(query, doc_contents)
        
        # 5. 过滤低分数结果并拼接
        filtered_results = [doc for doc in reranked_docs if doc.score >= min_score]
        
        if not filtered_results:
            return "未找到相关文档。"
        
        final_result = "\n\n".join(result.content for result in filtered_results)
        logger.info(f"RAG查询完成，返回 {len(filtered_results)} 个相关文档")
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
