"""基于 LangChain 的聊天智能体实现"""
from typing import List, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from loguru import logger


class ChatAgent:
    """基于 LangChain 的聊天智能体"""
    
    def __init__(self, model: ChatOpenAI, system_prompt: Optional[str] = None, tools: Optional[List[BaseTool]] = None):
        """
        初始化 ChatAgent
        
        Args:
            model: LLM模型实例
            system_prompt: 系统提示词
            tools: 工具列表（可选）
        """
        self.model = model
        self.system_prompt = system_prompt or "你是一个有用的AI助手。"
        self.tools = tools or []
        
        # 使用 create_react_agent 创建 Agent Executor
        self.agent_executor = create_react_agent(
            model=model,
            tools=self.tools,
            prompt=self.system_prompt
        )
        logger.info(f"ChatAgent 初始化成功，加载了 {len(self.tools)} 个工具")
    
    async def run(self, user_input: str, history: Optional[List[dict]] = None, context: Optional[str] = None) -> str:
        """
        执行 ChatAgent，处理用户输入
        
        Args:
            user_input: 用户输入
            history: 历史消息列表，格式: [{"role": "user/assistant", "content": "..."}]
            context: RAG检索的上下文信息（可选）
            
        Returns:
            AI的回复
        """
        try:
            # 构建系统提示词（包含RAG上下文）
            if context:
                system_prompt = f"{self.system_prompt}\n\n请根据以下参考信息回答问题。如果参考信息不足以回答问题，请基于你的知识回答，但可以提及参考信息。\n{context}"
            else:
                system_prompt = self.system_prompt
            
            # 构建输入消息
            messages = []
            if history and len(history) > 0:
                for msg in history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            messages.append(HumanMessage(content=user_input))
            
            # 执行 Agent
            result = await self.agent_executor.ainvoke({"messages": messages})
            response = result["messages"][-1].content
            
            logger.info(f"ChatAgent处理成功，回复长度: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"ChatAgent执行失败: {e}")
            raise
    
    async def stream_run(self, user_input: str, history: Optional[List[dict]] = None, context: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        流式执行 ChatAgent，处理用户输入
        
        Args:
            user_input: 用户输入
            history: 历史消息列表，格式: [{"role": "user/assistant", "content": "..."}]
            context: RAG检索的上下文信息（可选）
            
        Yields:
            AI的回复片段
        """
        try:
            # 构建系统提示词（包含RAG上下文）
            if context:
                system_prompt = f"{self.system_prompt}\n\n请根据以下参考信息回答问题。如果参考信息不足以回答问题，请基于你的知识回答，但可以提及参考信息。\n{context}"
            else:
                system_prompt = self.system_prompt
            
            # 构建输入消息
            messages = []
            if history and len(history) > 0:
                for msg in history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            messages.append(HumanMessage(content=user_input))
            
            # 流式执行 Agent
            async for event in self.agent_executor.astream_events({"messages": messages}, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield content
            
        except Exception as e:
            logger.error(f"ChatAgent流式执行失败: {e}")
            raise
