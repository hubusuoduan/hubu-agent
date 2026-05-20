"""Milvus向量数据库客户端"""
from loguru import logger
from pymilvus import MilvusClient, DataType
from typing import Dict, Optional, List
import asyncio

from app.config import settings
from app.services.rag.embedding import get_embedding


class VectorDBClient:
    """Milvus向量数据库客户端"""
    
    def __init__(self):
        # 构建连接URI和token
        self.uri = f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
        self.token = f"{settings.MILVUS_USER}:{settings.MILVUS_PASSWORD}"
        self.dimension = settings.EMBEDDING_DIMENSION
        
        # 创建MilvusClient实例
        self.client = MilvusClient(uri=self.uri, token=self.token)
        logger.info(f"成功连接到Milvus: {self.uri}")
    
    async def create_collection(self, collection_name: str, dimension: int = None):
        """创建Milvus集合"""
        if dimension is None:
            dimension = self.dimension
        
        # 检查集合是否已存在
        if self.client.has_collection(collection_name):
            logger.info(f"集合 '{collection_name}' 已存在")
            # 如果已存在，确保它被加载到内存
            try:
                self.client.load_collection(collection_name)
            except Exception:
                pass  # 可能已经加载，忽略错误
            return
        
        try:
            # 构建schema
            schema = MilvusClient.create_schema(
                auto_id=True,  # 自动分配主键
                enable_dynamic_field=True  # 启用动态字段
            )
            
            # 添加字段
            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, max_length=256)
            schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=dimension)
            schema.add_field(field_name="file_id", datatype=DataType.VARCHAR, max_length=128)
            schema.add_field(field_name="file_name", datatype=DataType.VARCHAR, max_length=256)
            schema.add_field(field_name="knowledge_id", datatype=DataType.VARCHAR, max_length=128)
            
            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                consistency_level="Strong"
            )
            
            # 创建索引
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="embedding",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 128}
            )
            self.client.create_index(
                collection_name=collection_name,
                index_params=index_params
            )
            
            # 加载集合到内存（搜索和查询前必须执行）
            self.client.load_collection(collection_name)
            
            logger.info(f"成功创建集合: {collection_name}")
        
        except Exception as e:
            logger.error(f"创建集合 '{collection_name}' 失败: {e}")
            raise
    
    async def insert(self, collection_name: str, chunks: List[dict]) -> bool:
        """插入数据到集合"""
        # 如果集合不存在，先创建
        if not self.client.has_collection(collection_name):
            await self.create_collection(collection_name)
        
        try:
            # 生成嵌入向量
            content_list = [chunk['content'] for chunk in chunks]
            embedding_list = await get_embedding(content_list)
            
            # 组织数据
            data = []
            for i, chunk in enumerate(chunks):
                data.append({
                    "chunk_id": chunk['chunk_id'],
                    "content": chunk['content'],
                    "embedding": embedding_list[i],
                    "file_id": chunk['file_id'],
                    "file_name": chunk['file_name'],
                    "knowledge_id": chunk['knowledge_id']
                })
            
            # 插入数据
            self.client.insert(collection_name=collection_name, data=data)
            
            logger.info(f"成功插入 {len(chunks)} 个文档块到集合 '{collection_name}'")
            return True
        
        except Exception as e:
            logger.error(f"插入数据到集合 '{collection_name}' 失败: {e}")
            return False
    
    async def search(self, query_embedding: List[float], collection_name: str, top_k: int = 5) -> List[dict]:
        """在集合中搜索相似数据"""
        try:
            # 搜索
            results = self.client.search(
                collection_name=collection_name,
                data=[query_embedding],
                anns_field="embedding",
                limit=top_k,
                output_fields=["content", "chunk_id", "file_id", "file_name", "knowledge_id"],
                search_params={
                    "metric_type": "L2",
                    "params": {"nprobe": 16}
                }
            )
            
            # 整理结果
            documents = []
            for hit in results[0]:
                documents.append({
                    "content": hit['entity'].get('content'),
                    "chunk_id": hit['entity'].get('chunk_id'),
                    "file_id": hit['entity'].get('file_id'),
                    "file_name": hit['entity'].get('file_name'),
                    "knowledge_id": hit['entity'].get('knowledge_id'),
                    "score": hit['distance']
                })
            
            return documents
        
        except Exception as e:
            logger.error(f"在集合 '{collection_name}' 中搜索失败: {e}")
            return []
    
    async def delete_by_file_id(self, file_id: str, collection_name: str) -> bool:
        """根据文件ID删除数据"""
        try:
            # 查询要删除的记录
            results = self.client.query(
                collection_name=collection_name,
                filter=f'file_id == "{file_id}"',
                output_fields=["id"]
            )
            
            if results:
                # 提取ID列表
                delete_ids = [result['id'] for result in results]
                
                # 删除记录
                self.client.delete(
                    collection_name=collection_name,
                    filter=f"id in {delete_ids}"
                )
                
                logger.info(f'成功删除文件ID {file_id} 的 {len(delete_ids)} 个文档')
            else:
                logger.info(f'未找到文件ID {file_id} 的文档')
            
            return True
        
        except Exception as e:
            logger.error(f'从集合 {collection_name} 删除文件ID {file_id} 出错: {e}')
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            self.client.drop_collection(collection_name)
            logger.info(f"成功删除集合 '{collection_name}'")
            return True
        
        except Exception as e:
            logger.error(f"删除集合 '{collection_name}' 失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        try:
            self.client.close()
            logger.info("Milvus连接已关闭")
        except Exception as e:
            logger.error(f"关闭Milvus连接出错: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 全局Milvus客户端实例
vector_db_client = VectorDBClient()
