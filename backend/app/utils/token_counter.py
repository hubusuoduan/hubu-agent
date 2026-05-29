"""Token 计算工具 - 用于精确计算消息的token数量"""
from typing import List, Dict
import tiktoken
from loguru import logger


class TokenCounter:
    """Token 计数器
    
    使用 tiktoken 库精确计算消息的token数量，
    用于上下文长度控制和动态截断。
    """
    
    def __init__(self, model_name: str = None, state: dict = None):
        """
        初始化 Token 计数器
        
        Args:
            model_name: 模型名称，用于选择合适的encoder
            state: Graph 状态（供 SummaryAgent 构建提示词）
        """
        self.model_name = model_name or "gpt-3.5-turbo"
        self.state = state
        try:
            # 尝试获取对应模型的encoder
            self.encoder = tiktoken.encoding_for_model(self.model_name)
            logger.info(f"TokenCounter 初始化成功，模型: {self.model_name}")
        except KeyError:
            # 如果模型不支持，使用默认的 cl100k_base (GPT-4/GPT-3.5)
            logger.warning(f"模型 {self.model_name} 不支持，使用默认 encoder")
            self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            token数量
        """
        return len(self.encoder.encode(text))
    
    def count_message_tokens(self, messages: List[Dict]) -> int:
        """
        计算消息列表的总token数量
        
        Args:
            messages: 消息列表，格式: [{"role": "user/assistant/system", "content": "..."}]
            
        Returns:
            总token数量
        """
        total_tokens = 0
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # 计算role和content的token
            role_tokens = self.count_tokens(role)
            content_tokens = self.count_tokens(content)
            
            # 每条消息有额外的 overhead
            total_tokens += role_tokens + content_tokens + 3  # 3是固定overhead
        
        # 每条消息序列有额外overhead
        total_tokens += 3
        
        return total_tokens
    
    async def truncate_messages_by_tokens(
        self, 
        messages: List[Dict], 
        max_tokens: int,
        preserve_first: bool = False
    ) -> List[Dict]:
        """
        根据token限制截断消息列表
        
        策略：
        1. 如果preserve_first=True且第一条是摘要，则保留摘要
        2. 从后往前遍历，找到需要丢弃的消息
        3. 使用 SummaryAgent 为丢弃的消息生成二次摘要
        4. 将二次摘要插入到原始摘要后面（不计算其token占用）
        5. 优先保留后面的消息（更新鲜的上下文）
        
        Args:
            messages: 消息列表
            max_tokens: 最大token数
            preserve_first: 是否保留第一条消息（仅当它是摘要时）
            
        Returns:
            截断后的消息列表
        """
        if not messages:
            return []
        
        # 检查第一条是否是摘要
        is_summary = False
        if preserve_first and len(messages) > 0:
            first_content = messages[0].get("content", "")
            is_summary = "[历史对话摘要]" in first_content
        
        # 只有第一条是摘要时才分离
        first_message = None
        remaining_messages = messages
        
        if is_summary:
            first_message = messages[0]
            remaining_messages = messages[1:]
            logger.info(f"检测到摘要消息，将保留")
        
        # 从后往前累加token，找到可以保留的消息和需要丢弃的消息
        retained_messages = []
        discarded_messages = []
        current_tokens = 0
        
        for msg in reversed(remaining_messages):
            msg_tokens = self.count_message_tokens([msg])
            
            if current_tokens + msg_tokens <= max_tokens:
                retained_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                # 这条消息及之前的都需要丢弃
                discarded_messages.insert(0, msg)
        
        # 如果有被丢弃的消息，使用 SummaryAgent 生成二次摘要
        final_messages = retained_messages
        if discarded_messages and self.state:
            try:
                from app.core.agents.llm import SummaryAgent

                # 构建临时 state 供 SummaryAgent 使用
                summary_state = dict(self.state)
                summary_state["messages"] = discarded_messages

                summary_text = await SummaryAgent.summarize(summary_state)
                
                if summary_text:
                    # 创建二次摘要消息（不计算token占用）
                    summary_msg = {
                        "role": "user",
                        "content": f"[历史对话摘要]\n{summary_text}\n\n请基于以上摘要继续回答。"
                    }
                    # 直接插入到保留消息前面，不检查token
                    final_messages.insert(0, summary_msg)
                    logger.info(f"为 {len(discarded_messages)} 条丢弃消息生成二次摘要")
                else:
                    logger.warning("二次摘要生成返回空字符串")
            except Exception as e:
                logger.error(f"生成二次摘要失败: {e}")
        elif discarded_messages:
            logger.info(f"丢弃 {len(discarded_messages)} 条消息（无 state，无法生成摘要）")
        
        # 如果有原始摘要，添加到最开头
        if first_message:
            final_messages.insert(0, first_message)
        
        logger.info(f"Token截断: {len(messages)} -> {len(final_messages)} 条消息")
        return final_messages
    
    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """
        截断单条消息的内容
        
        Args:
            content: 原始内容
            max_tokens: 最大token数
            
        Returns:
            截断后的内容
        """
        tokens = self.encoder.encode(content)
        
        if len(tokens) <= max_tokens:
            return content
        
        # 截断token并解码
        truncated_tokens = tokens[:max_tokens]
        return self.encoder.decode(truncated_tokens)
