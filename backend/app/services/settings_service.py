"""系统配置服务 - 支持前端动态修改部分配置

读取优先级：Redis 覆盖值 > .env 默认值
业务代码通过 settings.XXX 访问时自动走动态覆盖（由 Settings.__getattribute__ 实现）
"""
from typing import Any, Dict, List, Optional

from loguru import logger

from app.config import settings
from app.services.redis_client import RedisClient


# 可配置字段的元信息定义
CONFIGURABLE_FIELDS: Dict[str, Dict[str, Any]] = {
    # ── 对话历史 ──
    "MAX_HISTORY_ROUNDS": {
        "type": "int", "min": 1, "max": 50,
        "group": "对话历史", "desc": "最大保留对话轮数"
    },
    "ENABLE_HISTORY_SUMMARY": {
        "type": "bool",
        "group": "对话历史", "desc": "是否启用历史摘要"
    },
    "SUMMARY_THRESHOLD": {
        "type": "int", "min": 5, "max": 100,
        "group": "对话历史", "desc": "触发摘要的消息条数阈值"
    },

    # ── 上下文控制 ──
    "MAX_CONTEXT_TOKENS": {
        "type": "int", "min": 1000, "max": 128000,
        "group": "上下文控制", "desc": "最大上下文token数"
    },
    "RESERVE_FOR_RESPONSE": {
        "type": "int", "min": 500, "max": 8000,
        "group": "上下文控制", "desc": "预留响应token数"
    },
    "ENABLE_TOKEN_CONTROL": {
        "type": "bool",
        "group": "上下文控制", "desc": "是否启用token控制"
    },
    "MERGE_MAX_CONTEXT_LENGTH": {
        "type": "int", "min": 1000, "max": 128000,
        "group": "上下文控制", "desc": "综合处理节点合并后上下文最大字符数"
    },

    # ── RAG检索 ──
    "RAG_TOP_K": {
        "type": "int", "min": 1, "max": 30,
        "group": "RAG检索", "desc": "每个知识库检索的文档数量"
    },
    "RAG_MIN_SCORE": {
        "type": "float", "min": 0.0, "max": 1.0,
        "group": "RAG检索", "desc": "最小分数阈值"
    },
    "RAG_RERANKER_TOP_N": {
        "type": "int", "min": 1, "max": 30,
        "group": "RAG检索", "desc": "参与重排序的文档数量"
    },

}


def _cast_value(raw: str, field_type: str) -> Any:
    """将 Redis 中存储的字符串转换为对应类型"""
    if field_type == "int":
        return int(raw)
    elif field_type == "float":
        return float(raw)
    elif field_type == "bool":
        return raw.lower() in ("true", "1", "yes")
    return raw


class SettingsService:
    """系统配置服务"""

    REDIS_PREFIX = "app_settings:"

    # 进程内缓存，避免每次访问属性都查 Redis
    _cache: Dict[str, Any] = {}
    _cache_loaded: bool = False

    @classmethod
    def _redis_key(cls, key: str) -> str:
        return f"{cls.REDIS_PREFIX}{key}"

    @classmethod
    def load_cache(cls):
        """从 Redis 加载所有覆盖值到进程内缓存（启动时调用一次）"""
        cls._cache.clear()
        try:
            client = RedisClient.get_client()
            # 用 SCAN 批量获取所有 app_settings:* 的键值
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor, match=f"{cls.REDIS_PREFIX}*", count=100)
                if keys:
                    values = client.mget(keys)
                    for k, v in zip(keys, values):
                        if v is not None:
                            short_key = k.decode() if isinstance(k, bytes) else k
                            short_key = short_key.replace(cls.REDIS_PREFIX, "")
                            cls._cache[short_key] = v
                if cursor == 0:
                    break
            cls._cache_loaded = True
            logger.info(f"配置缓存加载完成，共 {len(cls._cache)} 项覆盖值")
        except Exception as e:
            logger.warning(f"配置缓存加载失败，将使用默认值: {e}")
            cls._cache_loaded = True

    @classmethod
    def get_effective_value(cls, key: str) -> Optional[Any]:
        """获取配置的生效值：进程缓存 > .env默认值"""
        if key in cls._cache:
            raw = cls._cache[key]
            field_type = CONFIGURABLE_FIELDS[key]["type"]
            return _cast_value(raw, field_type)
        # 回退到 settings 默认值
        return object.__getattribute__(settings, key)

    @classmethod
    def set_value(cls, key: str, value: Any) -> Dict[str, Any]:
        """设置配置覆盖值到 Redis + 更新进程缓存"""
        if key not in CONFIGURABLE_FIELDS:
            raise ValueError(f"配置项 '{key}' 不允许前端修改")

        field_meta = CONFIGURABLE_FIELDS[key]
        field_type = field_meta["type"]

        # 类型转换与校验
        try:
            if field_type == "int":
                value = int(value)
            elif field_type == "float":
                value = float(value)
            elif field_type == "bool":
                if isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")
                else:
                    value = bool(value)
        except (ValueError, TypeError):
            raise ValueError(f"配置项 '{key}' 的值类型错误，期望 {field_type}")

        # 范围校验
        if "min" in field_meta and value < field_meta["min"]:
            raise ValueError(f"配置项 '{key}' 的值不能小于 {field_meta['min']}")
        if "max" in field_meta and value > field_meta["max"]:
            raise ValueError(f"配置项 '{key}' 的值不能大于 {field_meta['max']}")

        # 写入 Redis（不过期）
        try:
            RedisClient.set(cls._redis_key(key), str(value), expiration=0)
        except Exception as e:
            logger.error(f"Redis写入配置失败 [{key}]: {e}")
            raise RuntimeError(f"配置保存失败: {e}")

        # 更新进程缓存
        cls._cache[key] = str(value)
        logger.info(f"配置已更新: {key} = {value}")
        return {"key": key, "value": value}

    @classmethod
    def reset_value(cls, key: str) -> bool:
        """重置单个配置为默认值（删除Redis覆盖 + 清除缓存）"""
        if key not in CONFIGURABLE_FIELDS:
            raise ValueError(f"配置项 '{key}' 不允许前端修改")

        try:
            RedisClient.delete(cls._redis_key(key))
            cls._cache.pop(key, None)
            logger.info(f"配置已重置: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis删除配置失败 [{key}]: {e}")
            raise RuntimeError(f"配置重置失败: {e}")

    @classmethod
    def reset_all(cls) -> int:
        """重置所有配置为默认值"""
        count = 0
        for key in list(cls._cache.keys()):
            try:
                RedisClient.delete(cls._redis_key(key))
                count += 1
            except Exception as e:
                logger.error(f"重置配置失败 [{key}]: {e}")
        cls._cache.clear()
        logger.info(f"已重置 {count} 项配置")
        return count

    @classmethod
    def get_all_settings(cls) -> List[Dict[str, Any]]:
        """获取所有可配置项（含当前值、默认值、元信息）"""
        result = []
        for key, meta in CONFIGURABLE_FIELDS.items():
            default_value = object.__getattribute__(settings, key)
            current_value = cls.get_effective_value(key)
            is_modified = (current_value != default_value)

            result.append({
                "key": key,
                "type": meta["type"],
                "group": meta["group"],
                "desc": meta["desc"],
                "default_value": default_value,
                "current_value": current_value,
                "is_modified": is_modified,
                "min": meta.get("min"),
                "max": meta.get("max"),
            })
        return result

    @classmethod
    def get_settings_grouped(cls) -> Dict[str, List[Dict[str, Any]]]:
        """获取按分组的配置项"""
        all_settings = cls.get_all_settings()
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for item in all_settings:
            group = item["group"]
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(item)
        return grouped
