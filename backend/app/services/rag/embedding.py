"""向量嵌入服务"""
import asyncio
from typing import Union, List
from loguru import logger
import dashscope
from app.config import settings

# 配置DashScope API密钥
dashscope.api_key = settings.EMBEDDING_API_KEY


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
        
        # 调用DashScope Embedding API
        response = dashscope.TextEmbedding.call(
            model=settings.EMBEDDING_MODEL,
            input=texts
        )
        
        if response.status_code == 200:
            embeddings = [
                item['embedding'] 
                for item in response.output['embeddings']
            ]
            
            logger.debug(f"成功获取 {len(embeddings)} 个向量嵌入")
            
            # 返回格式：单个字符串返回一维列表，列表返回二维列表
            return embeddings[0] if single else embeddings
        else:
            logger.error(f"Embedding API调用失败: {response.code} - {response.message}")
            raise Exception(f"Embedding API错误: {response.code} - {response.message}")
            
    except Exception as e:
        logger.error(f"获取embedding失败: {e}")
        raise
