"""向量嵌入服务"""
import asyncio
from typing import Union, List
from loguru import logger
import dashscope
from app.config import settings

# 配置DashScope API密钥
dashscope.api_key = settings.EMBEDDING_API_KEY

# DashScope Embedding API限制每次最多10条文本
EMBEDDING_BATCH_SIZE = 10


async def get_embedding(query: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
    """
    获取文本的向量嵌入

    Args:
        query: 单个字符串或字符串列表

    Returns:
        向量嵌入列表
    """
    try:
        # 统一处理为列表
        if isinstance(query, str):
            texts = [query]
            single = True
        else:
            texts = query
            single = False

        # 分批调用DashScope Embedding API，每批最多EMBEDDING_BATCH_SIZE条
        all_embeddings = []

        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i:i + EMBEDDING_BATCH_SIZE]
            logger.debug(f"Embedding API调用: 批次 {i // EMBEDDING_BATCH_SIZE + 1}, 文本数: {len(batch)}")

            response = dashscope.TextEmbedding.call(
                model=settings.EMBEDDING_MODEL,
                input=batch
            )

            if response.status_code == 200:
                batch_embeddings = [
                    item['embedding']
                    for item in response.output['embeddings']
                ]
                all_embeddings.extend(batch_embeddings)
            else:
                logger.error(f"Embedding API调用失败: {response.code} - {response.message}")
                raise Exception(f"Embedding API错误: {response.code} - {response.message}")

        # 返回格式：单个字符串返回一维列表，列表返回二维列表
        return all_embeddings[0] if single else all_embeddings

    except Exception as e:
        logger.error(f"获取embedding失败: {e}")
        raise
