from pydantic_settings import BaseSettings
from pathlib import Path
from loguru import logger

# 获取 backend 目录路径
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """应用配置管理"""
    
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
    
    # Embedding配置
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-v3"
    
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
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
