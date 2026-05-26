import json
from typing import List, Optional
from pydantic_settings import BaseSettings
from pathlib import Path
from loguru import logger

# 获取 backend 目录路径
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """应用配置管理

    支持动态配置覆盖：当访问的属性名在 CONFIGURABLE_FIELDS 中时，
    自动从 Redis 覆盖层读取，业务代码无需任何改动。
    """

    # 应用基础配置
    APP_NAME: str = "Hubu Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "hubu_agent"

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # LLM配置
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_STREAM_CHUNK_TIMEOUT: int = 300  # 流式输出chunk超时（秒），thinking模型需调大

    # 多模型Provider配置（JSON字符串）
    LLM_PROVIDERS: str = "[]"

    @property
    def model_providers(self) -> List[dict]:
        """解析多模型Provider配置"""
        try:
            providers = json.loads(self.LLM_PROVIDERS)
            if isinstance(providers, list) and len(providers) > 0:
                return providers
        except (json.JSONDecodeError, TypeError):
            pass
        # 兜底：用旧的单模型配置生成一个默认Provider
        return [{
            "id": "default",
            "name": self.LLM_MODEL,
            "api_key": self.LLM_API_KEY,
            "base_url": self.LLM_BASE_URL,
            "model": self.LLM_MODEL,
            "is_default": True
        }]

    @property
    def default_provider_id(self) -> str:
        """获取默认Provider的ID"""
        for p in self.model_providers:
            if p.get("is_default"):
                return p["id"]
        return self.model_providers[0]["id"] if self.model_providers else "default"

    # 对话历史管理配置
    MAX_HISTORY_ROUNDS: int = 10  # 最大保留对话轮数
    ENABLE_HISTORY_SUMMARY: bool = True  # 是否启用历史摘要
    SUMMARY_THRESHOLD: int = 20  # 触发摘要的消息条数阈值

    # 上下文长度控制配置
    MAX_CONTEXT_TOKENS: int = 8000  # 最大上下文token数
    RESERVE_FOR_RESPONSE: int = 2000  # 预留响应token数
    ENABLE_TOKEN_CONTROL: bool = True  # 是否启用token控制
    MERGE_MAX_CONTEXT_LENGTH: int = 8000  # 综合处理节点合并后上下文最大字符数

    # Embedding配置
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-v3"

    # Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    EMBEDDING_DIMENSION: int = 1024
    MILVUS_NPROBE: int = 32  # 向量检索时搜索的聚类中心数量

    # RAG检索配置
    RAG_TOP_K: int = 8  # 每个知识库检索的文档数量
    RAG_MIN_SCORE: float = 0.2  # 最小分数阈值
    RAG_RERANKER_TOP_N: int = 15  # 参与重排序的文档数量
    RAG_HYBRID_WEIGHTS: str = "0.4,0.6"  # BM25权重,语义权重(逗号分隔)

    # 长期记忆配置
    MEMORY_TOP_K: int = 5  # 记忆检索返回的最大数量
    MEMORY_MIN_SCORE: float = 0.3  # 记忆检索最低相似度阈值

    # Agent配置
    AGENT_MAX_ITERATIONS: int = 10  # Agent最大工具调用轮数，防止死循环

    # 工具配置
    WEATHER_API_KEY: str = ""  # 高德天气API Key
    WEATHER_API_ENDPOINT: str = "https://restapi.amap.com/v3/weather/weatherInfo"
    TAVILY_API_KEY: str = ""  # Tavily搜索API Key

    # 沙箱代码执行器配置（code_runner）
    SANDBOX_TIMEOUT: int = 30  # 默认超时（秒）
    SANDBOX_MAX_TIMEOUT: int = 120  # 最大超时（秒）
    SANDBOX_MAX_OUTPUT: int = 5000  # 最大输出字符数

    # 完整代码执行器配置（code_exec）
    CODE_EXEC_TIMEOUT: int = 60  # 默认超时（秒）
    CODE_EXEC_MAX_TIMEOUT: int = 300  # 最大超时（秒）
    CODE_EXEC_MAX_OUTPUT: int = 10000  # 最大输出字符数

    # 文件管理器配置（file_manager）

    FILE_MAX_SIZE: int = 52428800  # 单文件最大字节数（50MB）

    @property
    def file_workspace_path(self) -> Path:
        """获取文件工作区的绝对路径（固定为 backend/output）"""
        p = BACKEND_DIR / "output"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 包安装器配置（package_installer）
    PKG_ALLOW_PIP: bool = True  # 是否允许 pip install
    PKG_ALLOW_NPM: bool = True  # 是否允许 npm install
    PKG_PIP_TIMEOUT: int = 120  # pip 安装超时（秒）
    PKG_NPM_TIMEOUT: int = 120  # npm 安装超时（秒）
    PKG_ALLOW_LIST: str = ""  # 允许安装的包名（逗号分隔，留空不限制）
    PKG_DENY_LIST: str = ""  # 禁止安装的包名（逗号分隔）

    @property
    def pkg_allow_set(self) -> set:
        """获取允许安装的包名集合"""
        if not self.PKG_ALLOW_LIST.strip():
            return set()
        return {p.strip().lower() for p in self.PKG_ALLOW_LIST.split(",") if p.strip()}

    @property
    def pkg_deny_set(self) -> set:
        """获取禁止安装的包名集合"""
        return {p.strip().lower() for p in self.PKG_DENY_LIST.split(",") if p.strip()}

    # 日志配置
    LOG_LEVEL: str = "INFO"           # 控制台日志级别
    LOG_FILE_LEVEL: str = "WARNING"   # 文件日志级别（app.log最低级别，error.log固定ERROR+）

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __getattribute__(self, name: str):
        """动态属性访问：对可配置字段自动走 Redis 覆盖层"""
        # 先获取字段默认值
        value = super().__getattribute__(name)

        # 只对可配置字段做动态覆盖（避免递归和性能开销）
        if name in _CONFIGURABLE_FIELD_NAMES:
            try:
                from app.services.settings_service import SettingsService
                effective = SettingsService.get_effective_value(name)
                if effective is not None:
                    return effective
            except Exception:
                pass

        return value


# 可配置字段名称集合（用于 __getattribute__ 快速判断）
# 延迟初始化，避免循环导入
_CONFIGURABLE_FIELD_NAMES: set = set()


def _init_configurable_fields():
    """初始化可配置字段名称集合（启动时调用）"""
    global _CONFIGURABLE_FIELD_NAMES
    try:
        from app.services.settings_service import CONFIGURABLE_FIELDS
        _CONFIGURABLE_FIELD_NAMES = set(CONFIGURABLE_FIELDS.keys())
    except Exception:
        pass


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


def init_dynamic_settings():
    """初始化动态配置系统（应用启动时调用）

    1. 加载可配置字段名称集合
    2. 从 Redis 加载覆盖值到进程缓存
    """
    _init_configurable_fields()
    try:
        from app.services.settings_service import SettingsService
        SettingsService.load_cache()
        logger.info(f"动态配置系统初始化完成，共 {len(_CONFIGURABLE_FIELD_NAMES)} 个可配置字段")
    except Exception as e:
        logger.warning(f"动态配置系统初始化失败，将使用默认值: {e}")
