from typing import Optional
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

    # LLM配置已迁移至数据库 llm_provider 表，通过 /provider API 管理

    # 对话历史、上下文控制、RAG、记忆、Agent、代码执行等配置
    # 已移至 CONFIGURABLE_FIELDS（settings_service.py），默认值唯一来源

    # Embedding配置已迁移至数据库 embedding_provider 表，通过 /embedding-provider API 管理

    # Milvus配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    EMBEDDING_DIMENSION: int = 1024

    # 工具配置
    WEATHER_API_KEY: str = ""  # 高德天气API Key
    WEATHER_API_ENDPOINT: str = "https://restapi.amap.com/v3/weather/weatherInfo"
    TAVILY_API_KEY: str = ""  # Tavily搜索API Key

    # 代码执行器配置（code_exec）
    CODE_EXEC_MAX_OUTPUT: int = 10000  # 最大输出字符数

    # 文件管理器配置（file_manager）
    FILE_MAX_SIZE: int = 52428800  # 单文件最大字节数（50MB）

    def file_workspace_path(self, user_id: int | str | None = None) -> Path:
        """获取文件工作区的绝对路径

        Args:
            user_id: 用户ID，传入时返回 backend/output/{user_id}，不传返回 backend/output

        每个用户的文件存储在独立子目录中，避免互相干扰。
        """
        base = BACKEND_DIR / "output"
        base.mkdir(parents=True, exist_ok=True)
        if user_id is not None:
            p = base / str(user_id)
            p.mkdir(parents=True, exist_ok=True)
            return p
        return base

    @property
    def skills_base_path(self) -> Path:
        """获取系统 Skills 根目录的绝对路径（app/skills）"""
        p = BACKEND_DIR / "app" / "skills"
        return p

    def skills_path(self, user_id: int | str | None = None) -> Path:
        """获取用户 Skills 目录的绝对路径

        Args:
            user_id: 用户ID，传入时返回 skills/{user_id}，不传返回系统 skills 目录

        每个用户的自定义 Skill 存储在独立子目录中，系统 Skill 在 app/skills 下。
        用户目录下没有的 Skill 会 fallback 到系统目录。
        """
        if user_id is not None:
            p = BACKEND_DIR / "skills" / str(user_id)
            p.mkdir(parents=True, exist_ok=True)
            return p
        return self.skills_base_path

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
        extra = "ignore"  # .env 中的旧字段不再报错，自动忽略


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
