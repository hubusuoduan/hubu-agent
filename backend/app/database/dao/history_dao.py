"""对话历史DAO层"""
from typing import List, Optional
import json
from sqlmodel import select
from loguru import logger

from app.database.engine import async_engine
from app.database.models.history import HistoryTable
from app.services.redis_client import RedisClient
from sqlmodel.ext.asyncio.session import AsyncSession


class HistoryDao:
    """对话历史数据访问对象"""

    @classmethod
    async def create_history(
        cls, 
        dialog_id: str, 
        role: str, 
        content: str, 
        token_usage: int = 0
    ) -> HistoryTable:
        """
        创建历史记录
        
        Args:
            dialog_id: 对话ID
            role: 角色（user/assistant/system）
            content: 消息内容
            token_usage: Token使用量
            
        Returns:
            HistoryTable: 创建的历史记录
        """
        history = HistoryTable(
            dialog_id=dialog_id,
            role=role,
            content=content,
            token_usage=token_usage
        )
        
        async with AsyncSession(async_engine) as session:
            session.add(history)
            await session.commit()
            await session.refresh(history)
            logger.info(f"创建历史记录成功: {history.id}")
            
            # 增量更新Redis缓存
            try:
                cls._update_redis_cache(dialog_id, history)
            except Exception as e:
                logger.warning(f"更新Redis缓存失败: {e}")
            
            return history
    
    @classmethod
    def _update_redis_cache(cls, dialog_id: str, new_message: HistoryTable):
        """
        增量更新Redis缓存
        
        Args:
            dialog_id: 对话ID
            new_message: 新消息
        """
        # 更新常用的缓存key（recent:10 和 recent:50）
        for k in [10, 50]:
            cache_key = f"history:{dialog_id}:recent:{k}"
            try:
                cached_data = RedisClient.get(cache_key)
                if cached_data:
                    # 解析现有缓存
                    cached_list = json.loads(cached_data)
                    
                    # 添加新消息
                    new_item = {
                        "id": new_message.id,
                        "dialog_id": new_message.dialog_id,
                        "role": new_message.role,
                        "content": new_message.content,
                        "token_usage": new_message.token_usage
                    }
                    cached_list.append(new_item)
                    
                    # 保持最近k条
                    if len(cached_list) > k:
                        cached_list = cached_list[-k:]
                    
                    # 更新缓存
                    RedisClient.set(cache_key, json.dumps(cached_list), expiration=300)
                    logger.debug(f"增量更新Redis缓存: {cache_key}")
            except Exception as e:
                logger.warning(f"更新缓存 {cache_key} 失败: {e}")

    @classmethod
    async def get_history_by_dialog_id(
        cls, 
        dialog_id: str, 
        limit: int = 50
    ) -> List[HistoryTable]:
        """
        获取对话的历史记录
        
        Args:
            dialog_id: 对话ID
            limit: 限制返回数量
            
        Returns:
            List[HistoryTable]: 历史记录列表
        """
        async with AsyncSession(async_engine) as session:
            statement = (
                select(HistoryTable)
                .where(HistoryTable.dialog_id == dialog_id)
                .order_by(HistoryTable.create_time.desc())
                .limit(limit)
            )
            result = await session.execute(statement)
            histories = result.scalars().all()
            
            # 反转列表，使时间从旧到新
            histories.reverse()
            logger.info(f"获取对话历史成功: {dialog_id}, 数量: {len(histories)}")
            return histories

    @classmethod
    async def get_recent_messages(
        cls, 
        dialog_id: str, 
        k: int = 10
    ) -> List[HistoryTable]:
        """
        获取最近的k条消息（带Redis缓存）
        
        Args:
            dialog_id: 对话ID
            k: 消息数量
            
        Returns:
            List[HistoryTable]: 最近的消息列表
        """
        # 尝试从Redis获取缓存
        cache_key = f"history:{dialog_id}:recent:{k}"
        try:
            cached_data = RedisClient.get(cache_key)
            if cached_data:
                logger.info(f"从Redis缓存获取历史消息: {dialog_id}")
                # 反序列化缓存数据
                cached_list = json.loads(cached_data)
                # 转换为HistoryTable对象
                messages = []
                for item in cached_list:
                    msg = HistoryTable(
                        id=item.get("id", ""),
                        dialog_id=item.get("dialog_id", dialog_id),
                        role=item.get("role", ""),
                        content=item.get("content", ""),
                        token_usage=item.get("token_usage", 0)
                    )
                    messages.append(msg)
                return messages
        except Exception as e:
            logger.warning(f"Redis缓存读取失败，降级到数据库: {e}")
        
        # Redis未命中，从数据库查询
        async with AsyncSession(async_engine) as session:
            statement = (
                select(HistoryTable)
                .where(HistoryTable.dialog_id == dialog_id)
                .order_by(HistoryTable.create_time.desc())
                .limit(k)
            )
            result = await session.execute(statement)
            messages = result.scalars().all()
            
            # 保持时间顺序（从旧到新）
            messages.reverse()
            
            # 写入Redis缓存（过期时间5分钟）
            try:
                cache_data = [
                    {
                        "id": msg.id,
                        "dialog_id": msg.dialog_id,
                        "role": msg.role,
                        "content": msg.content,
                        "token_usage": msg.token_usage
                    }
                    for msg in messages
                ]
                RedisClient.set(cache_key, json.dumps(cache_data), expiration=300)
                logger.info(f"历史消息已缓存到Redis: {dialog_id}")
            except Exception as e:
                logger.warning(f"Redis缓存写入失败: {e}")
            
            logger.info(f"获取最近消息成功: {dialog_id}, 数量: {len(messages)}")
            return messages

    @classmethod
    async def delete_history_by_dialog_id(cls, dialog_id: str) -> bool:
        """
        删除对话的所有历史记录
        
        Args:
            dialog_id: 对话ID
            
        Returns:
            bool: 是否删除成功
        """
        async with AsyncSession(async_engine) as session:
            statement = select(HistoryTable).where(
                HistoryTable.dialog_id == dialog_id
            )
            result = await session.execute(statement)
            histories = result.scalars().all()
            
            for history in histories:
                await session.delete(history)
            
            await session.commit()
            logger.info(f"删除对话历史成功: {dialog_id}, 数量: {len(histories)}")
            return True
