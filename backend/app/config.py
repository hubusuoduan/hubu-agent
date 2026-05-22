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
    
    # 对话历史管理配置
    MAX_HISTORY_ROUNDS: int = 10  # 最大保留对话轮数
    ENABLE_HISTORY_SUMMARY: bool = True  # 是否启用历史摘要
    SUMMARY_THRESHOLD: int = 20  # 触发摘要的消息条数阈值
    
    # 上下文长度控制配置
    MAX_CONTEXT_TOKENS: int = 8000  # 最大上下文token数
    RESERVE_FOR_RESPONSE: int = 2000  # 预留响应token数
    ENABLE_TOKEN_CONTROL: bool = True  # 是否启用token控制
    
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
