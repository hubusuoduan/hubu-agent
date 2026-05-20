"""向量存储服务 - 基于Milvus"""
from typing import List, Dict, Optional
from loguru import logger

from app.services.rag.milvus_client import vector_db_client


class MilvusVectorStore:
    """基于Milvus的向量存储"""
    
    def __init__(self):
        self.client = vector_db_client
    
    async def add_documents(self, collection_name: str, chunks: List[dict]) -> bool:
        """
        添加文档到向量存储
        
        Args:
            collection_name: 集合名称（通常使用knowledge_id）
            chunks: 文档块列表，每个chunk包含:
                - chunk_id: 块ID
                - content: 文本内容
                - file_id: 文件ID
                - file_name: 文件名
                - knowledge_id: 知识库ID
        
        Returns:
            是否成功
        """
        return await self.client.insert(collection_name, chunks)
    
    async def search(self, query_embedding: List[float], collection_name: str, top_k: int = 5) -> List[dict]:
        """
        向量检索
        
        Args:
            query_embedding: 查询向量
            collection_name: 集合名称
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表，每个结果包含content, chunk_id, score等字段
        """
        return await self.client.search(query_embedding, collection_name, top_k)
    
    async def delete_by_file_id(self, file_id: str, collection_name: str) -> bool:
        """
        根据文件ID删除文档
        
        Args:
            file_id: 文件ID
            collection_name: 集合名称
            
        Returns:
            是否成功
        """
        return await self.client.delete_by_file_id(file_id, collection_name)


# 全局向量存储实例
vector_store = MilvusVectorStore()
