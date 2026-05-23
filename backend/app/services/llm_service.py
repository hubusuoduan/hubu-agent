"""LLM模型服务"""
from typing import Optional
from langchain_openai import ChatOpenAI
from loguru import logger


class LLMService:
    """LLM服务类，管理语言模型"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_model(cls, api_key: str, base_url: str, model_name: str) -> ChatOpenAI:
        """
        获取LLM模型实例
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
            
        Returns:
            ChatOpenAI 模型实例
        """
        if cls._model is None:
            try:
                cls._model = ChatOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    model=model_name,
                    temperature=0.7,
                    streaming=True,
                    stream_usage=True
                )
                logger.info(f"LLM模型初始化成功: {model_name}")
            except Exception as e:
                logger.error(f"LLM模型初始化失败: {e}")
                raise
        return cls._model
    
    @classmethod
    def reset_model(cls):
        """重置模型实例"""
        cls._model = None
