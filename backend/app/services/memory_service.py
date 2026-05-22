"""长期记忆服务 - 基于 Milvus 向量数据库"""
import uuid
import time
from typing import List, Optional, Dict
from loguru import logger
from pymilvus import MilvusClient, DataType

from app.config import settings
from app.services.rag.embedding import get_embedding


class MemoryService:
    """用户长期记忆服务

    使用 Milvus 存储和检索用户的长期记忆信息，
    包括用户偏好、个人特征、重要事实等。
    """

    COLLECTION_NAME = "user_memory"

    def __init__(self):
        self.uri = f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
        self.token = f"{settings.MILVUS_USER}:{settings.MILVUS_PASSWORD}"
        self.dimension = settings.EMBEDDING_DIMENSION
        self.client = MilvusClient(uri=self.uri, token=self.token)
        self._ensure_collection()

    def _ensure_collection(self):
        """确保 user_memory 集合存在"""
        if self.client.has_collection(self.COLLECTION_NAME):
            try:
                self.client.load_collection(self.COLLECTION_NAME)
            except Exception:
                pass
            return

        try:
            schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=True
            )

            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="memory_id", datatype=DataType.VARCHAR, max_length=128)
            schema.add_field(field_name="user_id", datatype=DataType.INT64)
            schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=2048)
            schema.add_field(field_name="memory_type", datatype=DataType.VARCHAR, max_length=64)
            schema.add_field(field_name="source_dialog_id", datatype=DataType.VARCHAR, max_length=128)
            schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=self.dimension)
            schema.add_field(field_name="created_at", datatype=DataType.INT64)

            # 创建集合
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
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
            # 为 user_id 创建标量索引，加速过滤
            index_params.add_index(
                field_name="user_id",
                index_type="INVERTED"
            )
            self.client.create_index(
                collection_name=self.COLLECTION_NAME,
                index_params=index_params
            )

            self.client.load_collection(self.COLLECTION_NAME)
            logger.info(f"成功创建长期记忆集合: {self.COLLECTION_NAME}")

        except Exception as e:
            logger.error(f"创建长期记忆集合失败: {e}")
            raise

    async def search_memories(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict]:
        """检索与查询相关的用户记忆

        Args:
            user_id: 用户ID
            query: 查询文本
            top_k: 返回最相似的K条记忆
            min_score: 最低相似度阈值

        Returns:
            相关记忆列表，每条包含 content, memory_type, score
        """
        try:
            # 生成查询向量
            query_embedding = await get_embedding(query)

            # 搜索参数
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": settings.MILVUS_NPROBE}
            }

            # 执行搜索，按 user_id 过滤
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                data=[query_embedding],
                anns_field="embedding",
                limit=top_k,
                output_fields=["memory_id", "content", "memory_type", "source_dialog_id", "created_at"],
                search_params=search_params,
                filter=f'user_id == {user_id}'
            )

            # 整理结果
            memories = []
            for hit in results[0]:
                distance = hit["distance"]
                score = 1.0 / (1.0 + distance)

                if score >= min_score:
                    memories.append({
                        "memory_id": hit["entity"].get("memory_id"),
                        "content": hit["entity"].get("content"),
                        "memory_type": hit["entity"].get("memory_type"),
                        "source_dialog_id": hit["entity"].get("source_dialog_id"),
                        "created_at": hit["entity"].get("created_at"),
                        "score": score
                    })

            logger.info(f"用户 {user_id} 记忆检索: 查询='{query[:30]}...', 命中 {len(memories)} 条")
            return memories

        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            return []

    async def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "fact",
        source_dialog_id: str = ""
    ) -> Optional[str]:
        """添加一条用户记忆

        Args:
            user_id: 用户ID
            content: 记忆内容
            memory_type: 记忆类型 (preference/fact/insight)
            source_dialog_id: 来源对话ID

        Returns:
            记忆ID，失败返回 None
        """
        try:
            # 确保 user_id 为整数（Milvus schema 定义为 INT64）
            user_id = int(user_id)
            source_dialog_id = str(source_dialog_id)

            # 先检查是否和已有记忆重复
            is_dup, dup_id = await self._check_duplicate(user_id, content)
            if is_dup:
                logger.info(f"记忆重复，跳过写入: {content[:30]}... (重复ID: {dup_id})")
                return None

            # 生成向量
            embedding = await get_embedding(content)

            # 生成唯一ID
            memory_id = str(uuid.uuid4())

            # 插入数据
            data = [{
                "memory_id": memory_id,
                "user_id": user_id,
                "content": content,
                "memory_type": memory_type,
                "source_dialog_id": source_dialog_id,
                "embedding": embedding,
                "created_at": int(time.time())
            }]

            self.client.insert(
                collection_name=self.COLLECTION_NAME,
                data=data
            )

            logger.info(f"成功写入用户记忆: user={user_id}, type={memory_type}, content='{content[:30]}...'")
            return memory_id

        except Exception as e:
            logger.error(f"写入用户记忆失败: {e}")
            return None

    async def _check_duplicate(
        self,
        user_id: str,
        content: str,
        threshold: float = 0.85
    ) -> tuple:
        """检查记忆是否重复

        Args:
            user_id: 用户ID
            content: 待检查的记忆内容
            threshold: 相似度阈值，超过则认为重复

        Returns:
            (是否重复, 重复记忆的memory_id)
        """
        try:
            embedding = await get_embedding(content)

            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": settings.MILVUS_NPROBE}
            }

            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                data=[embedding],
                anns_field="embedding",
                limit=1,
                output_fields=["memory_id", "content"],
                search_params=search_params,
                filter=f'user_id == {user_id}'
            )

            if results and results[0]:
                hit = results[0][0]
                distance = hit["distance"]
                score = 1.0 / (1.0 + distance)

                if score >= threshold:
                    return True, hit["entity"].get("memory_id")

            return False, None

        except Exception as e:
            logger.error(f"记忆去重检查失败: {e}")
            return False, None

    async def delete_memory(self, memory_id: str) -> bool:
        """删除一条记忆

        Args:
            memory_id: 记忆ID

        Returns:
            是否删除成功
        """
        try:
            # 先查询主键 id
            results = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=f'memory_id == "{memory_id}"',
                output_fields=["id"]
            )

            if results:
                delete_ids = [r["id"] for r in results]
                self.client.delete(
                    collection_name=self.COLLECTION_NAME,
                    filter=f"id in {delete_ids}"
                )
                logger.info(f"成功删除记忆: {memory_id}")
                return True
            else:
                logger.info(f"未找到记忆: {memory_id}")
                return False

        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False

    async def list_memories(self, user_id: str, limit: int = 100) -> List[Dict]:
        """列出用户所有记忆

        Args:
            user_id: 用户ID
            limit: 最大返回数量

        Returns:
            记忆列表
        """
        try:
            results = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=f'user_id == {user_id}',
                output_fields=["memory_id", "content", "memory_type", "source_dialog_id", "created_at"],
                limit=limit
            )

            return results

        except Exception as e:
            logger.error(f"列出用户记忆失败: {e}")
            return []

    async def add_memory_manual(
        self,
        user_id: int,
        content: str,
        memory_type: str = "fact"
    ) -> Optional[str]:
        """手动添加一条用户记忆（不走去重检查，由用户主动添加）

        Args:
            user_id: 用户ID
            content: 记忆内容
            memory_type: 记忆类型

        Returns:
            记忆ID，失败返回 None
        """
        try:
            embedding = await get_embedding(content)
            memory_id = str(uuid.uuid4())

            data = [{
                "memory_id": memory_id,
                "user_id": user_id,
                "content": content,
                "memory_type": memory_type,
                "source_dialog_id": "manual",
                "embedding": embedding,
                "created_at": int(time.time())
            }]

            self.client.insert(
                collection_name=self.COLLECTION_NAME,
                data=data
            )

            logger.info(f"手动写入用户记忆: user={user_id}, type={memory_type}")
            return memory_id

        except Exception as e:
            logger.error(f"手动写入记忆失败: {e}")
            return None

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> bool:
        """更新一条记忆（删除旧记录，重新写入）

        Args:
            memory_id: 记忆ID
            content: 新内容（可选）
            memory_type: 新类型（可选）

        Returns:
            是否更新成功
        """
        try:
            # 先查询旧记录
            results = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=f'memory_id == "{memory_id}"',
                output_fields=["id", "user_id", "content", "memory_type", "source_dialog_id", "created_at"]
            )

            if not results:
                logger.warning(f"未找到记忆: {memory_id}")
                return False

            old = results[0]
            new_content = content if content is not None else old["content"]
            new_type = memory_type if memory_type is not None else old["memory_type"]

            # 删除旧记录
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                filter=f'id in [{old["id"]}]'
            )

            # 重新写入
            embedding = await get_embedding(new_content)
            data = [{
                "memory_id": memory_id,
                "user_id": old["user_id"],
                "content": new_content,
                "memory_type": new_type,
                "source_dialog_id": old.get("source_dialog_id", ""),
                "embedding": embedding,
                "created_at": old.get("created_at", int(time.time()))
            }]

            self.client.insert(
                collection_name=self.COLLECTION_NAME,
                data=data
            )

            logger.info(f"更新记忆成功: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        try:
            self.client.close()
            logger.info("MemoryService Milvus连接已关闭")
        except Exception as e:
            logger.error(f"关闭MemoryService连接出错: {e}")


# 全局 MemoryService 实例
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """获取全局 MemoryService 实例"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
