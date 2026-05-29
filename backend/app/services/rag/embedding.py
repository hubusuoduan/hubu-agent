"""向量嵌入服务 - 用户级工厂模式"""
from typing import Union, List, Optional
from loguru import logger
import dashscope

# DashScope Embedding API限制每次最多10条文本
EMBEDDING_BATCH_SIZE = 10


class EmbeddingFactory:
    """Embedding工厂，按 user_id 获取用户配置

    从数据库读取用户的 EmbeddingProvider 配置，
    不传 user_id 时，自动从 current_user_id ContextVar 获取。
    用户未配置则抛出异常，要求用户先配置。
    """

    @classmethod
    def _get_user_id(cls) -> Optional[int]:
        """从 ContextVar 获取 user_id"""
        from app.middleware.user_context import current_user_id
        return current_user_id.get()

    @classmethod
    async def get_config(cls) -> dict:
        """获取用户的 Embedding 配置（从 ContextVar 自动获取 user_id）

        Returns:
            {"api_key": str, "base_url": str, "model": str}

        Raises:
            ValueError: 用户未配置 Embedding Provider
        """
        uid = cls._get_user_id()
        if uid:
            from app.database.dao.embedding_provider_dao import EmbeddingProviderDao
            provider = await EmbeddingProviderDao.get_by_user(uid)
            if provider:
                return {
                    "api_key": provider.api_key,
                    "base_url": provider.base_url,
                    "model": provider.model,
                }

        raise ValueError("未配置 Embedding 供应商，请在设置中配置 Embedding 模型")


async def get_embedding(query: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
    """
    获取文本的向量嵌入（从 ContextVar 自动获取 user_id）

    Args:
        query: 单个字符串或字符串列表

    Returns:
        向量嵌入列表
    """
    try:
        # 获取用户配置
        config = await EmbeddingFactory.get_config()

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
            logger.debug(f"Embedding API调用: 批次 {i // EMBEDDING_BATCH_SIZE + 1}, 文本数: {len(batch)}, model={config['model']}")

            # 每次调用前设置 api_key（支持多用户不同 key）
            dashscope.api_key = config["api_key"]

            response = dashscope.TextEmbedding.call(
                model=config["model"],
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
