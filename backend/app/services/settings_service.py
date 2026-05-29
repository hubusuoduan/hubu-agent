"""系统配置服务 - 用户级配置工厂模式

核心类 SettingsFactory：请求开始时 create_for_user() 一次性加载，请求过程中 get() 同步取值
默认值唯一来源：CONFIGURABLE_FIELDS 中的 default 字段，不再从 .env 读取
"""
import json
from typing import Any, Dict, List, Optional

from loguru import logger

from app.database.dao.user_setting_dao import UserSettingDao


# 可配置字段的元信息定义（default 为唯一默认值来源，不再从 .env 读取）
CONFIGURABLE_FIELDS: Dict[str, Dict[str, Any]] = {
    # ── 对话历史 ──
    "MAX_HISTORY_ROUNDS": {
        "type": "int", "default": 10, "min": 1, "max": 50,
        "group": "对话历史", "desc": "最大保留对话轮数"
    },
    "ENABLE_HISTORY_SUMMARY": {
        "type": "bool", "default": True,
        "group": "对话历史", "desc": "是否启用历史摘要"
    },
    "SUMMARY_THRESHOLD": {
        "type": "int", "default": 20, "min": 5, "max": 100,
        "group": "对话历史", "desc": "触发摘要的消息条数阈值"
    },

    # ── 上下文控制 ──
    "MAX_CONTEXT_TOKENS": {
        "type": "int", "default": 8000, "min": 1000, "max": 128000,
        "group": "上下文控制", "desc": "最大上下文token数"
    },
    "RESERVE_FOR_RESPONSE": {
        "type": "int", "default": 2000, "min": 500, "max": 8000,
        "group": "上下文控制", "desc": "预留响应token数"
    },
    "ENABLE_TOKEN_CONTROL": {
        "type": "bool", "default": True,
        "group": "上下文控制", "desc": "是否启用token控制"
    },
    "MERGE_MAX_CONTEXT_LENGTH": {
        "type": "int", "default": 8000, "min": 1000, "max": 128000,
        "group": "上下文控制", "desc": "综合处理节点合并后上下文最大字符数"
    },

    # ── RAG检索 ──
    "RAG_TOP_K": {
        "type": "int", "default": 8, "min": 1, "max": 30,
        "group": "RAG检索", "desc": "每个知识库检索的文档数量"
    },
    "RAG_MIN_SCORE": {
        "type": "float", "default": 0.2, "min": 0.0, "max": 1.0,
        "group": "RAG检索", "desc": "最小分数阈值"
    },
    "RAG_RERANKER_TOP_N": {
        "type": "int", "default": 15, "min": 1, "max": 30,
        "group": "RAG检索", "desc": "参与重排序的文档数量"
    },
    "RAG_HYBRID_WEIGHTS": {
        "type": "str", "default": "0.4,0.6",
        "group": "RAG检索", "desc": "混合检索权重(BM25权重,语义权重)"
    },
    "MILVUS_NPROBE": {
        "type": "int", "default": 32, "min": 1, "max": 128,
        "group": "RAG检索", "desc": "向量检索搜索的聚类中心数量"
    },

    # ── 长期记忆 ──
    "MEMORY_TOP_K": {
        "type": "int", "default": 5, "min": 1, "max": 20,
        "group": "长期记忆", "desc": "记忆检索返回的最大数量"
    },
    "MEMORY_MIN_SCORE": {
        "type": "float", "default": 0.3, "min": 0.0, "max": 1.0,
        "group": "长期记忆", "desc": "记忆检索最低相似度阈值"
    },

    # ── Agent ──
    "AGENT_MAX_ITERATIONS": {
        "type": "int", "default": 10, "min": 1, "max": 50,
        "group": "Agent", "desc": "Agent最大工具调用轮数，防止死循环"
    },
    "REVIEWER_MAX_RETRIES": {
        "type": "int", "default": 3, "min": 1, "max": 10,
        "group": "Agent", "desc": "Reviewer最大重试次数，防止死循环"
    },

    # ── 代码执行 ──
    "CODE_EXEC_TIMEOUT": {
        "type": "int", "default": 60, "min": 10, "max": 600,
        "group": "代码执行", "desc": "代码执行默认超时（秒）"
    },
    "CODE_EXEC_MAX_TIMEOUT": {
        "type": "int", "default": 300, "min": 60, "max": 600,
        "group": "代码执行", "desc": "代码执行最大超时（秒）"
    },

    # ── LLM ──
    "LLM_STREAM_CHUNK_TIMEOUT": {
        "type": "int", "default": 300, "min": 0, "max": 600,
        "group": "LLM", "desc": "流式chunk超时（秒），thinking模型需调大，0为禁用"
    },
}


def _get_default(key: str) -> Any:
    """从 CONFIGURABLE_FIELDS 获取默认值"""
    return CONFIGURABLE_FIELDS[key]["default"]


def _build_default_settings() -> Dict[str, Any]:
    """构建包含所有默认值的配置字典"""
    return {key: meta["default"] for key, meta in CONFIGURABLE_FIELDS.items()}


def _validate_value(key: str, value: Any) -> Any:
    """类型转换与范围校验，返回校验后的值"""
    if key not in CONFIGURABLE_FIELDS:
        raise ValueError(f"配置项 '{key}' 不允许前端修改")

    field_meta = CONFIGURABLE_FIELDS[key]
    field_type = field_meta["type"]

    # 类型转换
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
        elif field_type == "str":
            value = str(value)
    except (ValueError, TypeError):
        raise ValueError(f"配置项 '{key}' 的值类型错误，期望 {field_type}")

    # 范围校验
    if "min" in field_meta and value < field_meta["min"]:
        raise ValueError(f"配置项 '{key}' 的值不能小于 {field_meta['min']}")
    if "max" in field_meta and value > field_meta["max"]:
        raise ValueError(f"配置项 '{key}' 的值不能大于 {field_meta['max']}")

    return value


class SettingsFactory:
    """用户配置工厂 - 请求级生命周期管理

    用法：
        # 请求开始时（user_id 从 ContextVar 自动获取）
        await SettingsFactory.create_for_user()
        # 请求过程中（同步，无需 await）
        value = SettingsFactory.get(key="MAX_HISTORY_ROUNDS")
        # 请求结束时
        SettingsFactory.clear_user()
    """

    # 用户级配置缓存 {user_id: {key: value}}
    _user_settings: Dict[int, Dict[str, Any]] = {}

    @classmethod
    def _get_user_id(cls) -> int:
        """从 ContextVar 获取 user_id"""
        from app.middleware.user_context import current_user_id
        uid = current_user_id.get()
        if uid:
            return uid
        return 0

    @classmethod
    async def create_for_user(cls) -> Dict[str, Any]:
        """为用户加载配置（请求开始时调用，user_id 从 ContextVar 获取）

        从数据库读取一条 JSON 记录，合并默认值，存入内存缓存。
        如果数据库无记录，用默认值初始化并写入数据库。
        """
        uid = cls._get_user_id()
        defaults = _build_default_settings()

        # 从数据库读取
        db_data = await UserSettingDao.get_settings_json(uid)

        if db_data:
            # 合并：数据库值覆盖默认值，补全新增字段
            merged = {**defaults, **db_data}
        else:
            # 首次访问，用默认值初始化数据库
            merged = defaults.copy()
            await UserSettingDao.upsert(uid, json.dumps(merged, ensure_ascii=False))
            logger.info(f"用户配置首次初始化: user_id={uid}, 共 {len(merged)} 项")

        cls._user_settings[uid] = merged
        return merged

    @classmethod
    def get(cls, key: Optional[str] = None) -> Any:
        """同步获取配置值（请求过程中调用，无需 await，user_id 从 ContextVar 获取）

        从内存缓存直接取值，缓存不存在则返回默认值。
        """
        uid = cls._get_user_id()
        if key is None:
            # 不传 key，返回全部配置
            if uid in cls._user_settings:
                return cls._user_settings[uid].copy()
            return _build_default_settings()

        if uid in cls._user_settings and key in cls._user_settings[uid]:
            return cls._user_settings[uid][key]
        # 兜底：返回字段默认值
        if key in CONFIGURABLE_FIELDS:
            return _get_default(key)
        raise ValueError(f"配置项 '{key}' 不存在")

    @classmethod
    async def set_value(cls, user_id: int, key: str, value: Any) -> Dict[str, Any]:
        """设置单个配置值（读改写 JSON）"""
        value = _validate_value(key, value)

        # 确保缓存存在
        if user_id not in cls._user_settings:
            await cls.create_for_user()

        # 更新缓存
        cls._user_settings[user_id][key] = value

        # 写入数据库
        await UserSettingDao.upsert(
            user_id, json.dumps(cls._user_settings[user_id], ensure_ascii=False)
        )

        logger.info(f"用户配置已更新: user_id={user_id}, {key} = {value}")
        return {"key": key, "value": value}

    @classmethod
    async def reset_value(cls, user_id: int, key: str) -> bool:
        """重置单个配置为默认值"""
        if key not in CONFIGURABLE_FIELDS:
            raise ValueError(f"配置项 '{key}' 不允许前端修改")

        default_value = _get_default(key)

        # 更新缓存
        if user_id not in cls._user_settings:
            await cls.create_for_user()
        cls._user_settings[user_id][key] = default_value

        # 写入数据库
        await UserSettingDao.upsert(
            user_id, json.dumps(cls._user_settings[user_id], ensure_ascii=False)
        )

        logger.info(f"用户配置已重置: user_id={user_id}, {key}")
        return True

    @classmethod
    async def reset_all(cls, user_id: int) -> int:
        """重置用户所有配置为默认值"""
        defaults = _build_default_settings()
        cls._user_settings[user_id] = defaults.copy()

        # 写入数据库
        await UserSettingDao.upsert(
            user_id, json.dumps(defaults, ensure_ascii=False)
        )

        logger.info(f"用户配置已全部重置: user_id={user_id}, 共 {len(defaults)} 项")
        return len(defaults)

    @classmethod
    def clear_user(cls):
        """清除用户的配置缓存（请求结束时调用，user_id 从 ContextVar 获取）"""
        uid = cls._get_user_id()
        if uid in cls._user_settings:
            del cls._user_settings[uid]
            logger.debug(f"已清除用户 {uid} 的配置缓存")

    @classmethod
    def clear_all(cls):
        """清除所有缓存"""
        cls._user_settings.clear()
        logger.debug("已清除所有用户配置缓存")


class SettingsService:
    """系统配置服务 - 用户配置的 CRUD 操作（供 API 层调用）"""

    @classmethod
    async def init_user_settings(cls, user_id: int):
        """初始化用户默认配置（注册时调用，将所有默认值写入数据库）"""
        defaults = _build_default_settings()
        await UserSettingDao.upsert(user_id, json.dumps(defaults, ensure_ascii=False))
        logger.info(f"用户默认配置初始化完成: user_id={user_id}, 共 {len(defaults)} 项")

    @classmethod
    async def get_user_all_settings(cls, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有配置项（含元信息，供前端展示）"""
        # 确保缓存已加载（ContextVar 已由中间件设置，create_for_user 自动获取）
        if user_id not in SettingsFactory._user_settings:
            await SettingsFactory.create_for_user()

        user_data = SettingsFactory._user_settings[user_id]
        result = []
        for key, meta in CONFIGURABLE_FIELDS.items():
            default_value = meta["default"]
            current_value = user_data.get(key, default_value)
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
    async def get_user_settings_grouped(cls, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """获取按分组的用户配置项"""
        all_settings = await cls.get_user_all_settings(user_id)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for item in all_settings:
            group = item["group"]
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(item)
        return grouped

    @classmethod
    async def set_user_value(cls, user_id: int, key: str, value: Any) -> Dict[str, Any]:
        """设置用户级配置值"""
        return await SettingsFactory.set_value(user_id, key, value)

    @classmethod
    async def reset_user_value(cls, user_id: int, key: str) -> bool:
        """重置用户某个配置为默认值"""
        return await SettingsFactory.reset_value(user_id, key)

    @classmethod
    async def reset_user_all(cls, user_id: int) -> int:
        """重置用户所有配置为默认值"""
        return await SettingsFactory.reset_all(user_id)


# 兼容旧代码的别名（后续逐步替换后可删除）
UserConfig = SettingsFactory
