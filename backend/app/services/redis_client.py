"""Redis缓存服务"""
import redis
from loguru import logger
from typing import Optional

from app.config import settings


class RedisClient:
    """Redis客户端"""
    
    _client = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        获取Redis客户端实例
        
        Returns:
            redis.Redis: Redis客户端
        """
        if cls._client is None:
            try:
                cls._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                # 测试连接
                cls._client.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败: {e}")
                raise
        return cls._client
    
    @classmethod
    def set(cls, key: str, value: str, expiration: int = 3600) -> bool:
        """
        设置键值对
        
        Args:
            key: 键
            value: 值
            expiration: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        try:
            client = cls.get_client()
            if expiration > 0:
                result = client.setex(key, expiration, value)
            else:
                result = client.set(key, value)
            logger.debug(f"设置Redis键: {key}")
            return result
        except Exception as e:
            logger.error(f"设置Redis键失败: {e}")
            return False
    
    @classmethod
    def get(cls, key: str) -> Optional[str]:
        """
        获取键值
        
        Args:
            key: 键
            
        Returns:
            Optional[str]: 值
        """
        try:
            client = cls.get_client()
            value = client.get(key)
            logger.debug(f"获取Redis键: {key}")
            return value
        except Exception as e:
            logger.error(f"获取Redis键失败: {e}")
            return None
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """
        删除键
        
        Args:
            key: 键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            client = cls.get_client()
            result = client.delete(key)
            logger.debug(f"删除Redis键: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"删除Redis键失败: {e}")
            return False
    
    @classmethod
    def exists(cls, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键
            
        Returns:
            bool: 是否存在
        """
        try:
            client = cls.get_client()
            return client.exists(key) > 0
        except Exception as e:
            logger.error(f"检查Redis键失败: {e}")
            return False
    
    @classmethod
    def reset(cls):
        """重置Redis客户端"""
        if cls._client:
            cls._client.close()
            cls._client = None
            logger.info("Redis客户端已重置")
