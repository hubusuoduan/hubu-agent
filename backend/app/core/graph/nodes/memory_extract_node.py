"""长期记忆提取节点 - 从对话中提取并写入用户记忆"""
from typing import Optional
from loguru import logger

from app.core.graph.state import ChatState
from app.core.agents.memory_agent import MemoryAgent
from app.services.memory_service import get_memory_service
from app.services.llm_service import LLMService
from app.config import settings


# 全局 MemoryAgent 单例（无状态，无需按 session_id 缓存）
_memory_agent: Optional[MemoryAgent] = None


def get_memory_agent() -> MemoryAgent:
    """获取全局 MemoryAgent 实例（单例模式）"""
    global _memory_agent
    if _memory_agent is None:
        model = LLMService.get_model()
        _memory_agent = MemoryAgent(model=model)
        logger.info("创建全局 MemoryAgent 实例")
    return _memory_agent


async def memory_extract_node(state: ChatState) -> dict:
    """长期记忆提取节点

    在 LLM 生成回复后，分析本轮对话，
    提取需要长期记住的用户信息并写入 Milvus。

    Args:
        state: Graph 状态

    Returns:
        空字典（不修改状态，副作用是写入记忆）
    """
    try:
        user_input = state.get("user_input", "")
        response = state.get("response", "")
        user_id = state.get("user_id", "")
        session_id = state.get("session_id", "default")

        # 如果没有 user_id 或 response，跳过提取
        if not user_id or not response:
            logger.debug("缺少 user_id 或 response，跳过记忆提取")
            return {}

        # 获取用户已有记忆，用于 LLM 层面去重
        memory_service = get_memory_service()
        existing_result = await memory_service.list_memories(user_id=user_id, limit=50)
        existing_contents = [m.get("content", "") for m in existing_result.get("items", [])]

        # 使用 MemoryAgent 提取记忆（传入已有记忆避免重复提取）
        memory_agent = get_memory_agent()
        memories = await memory_agent.extract(
            user_input=user_input,
            assistant_response=response,
            existing_memories=existing_contents
        )

        if not memories:
            return {}

        # 写入 Milvus
        for m in memories:
            await memory_service.add_memory(
                user_id=user_id,
                content=m["content"],
                memory_type=m["type"],
                source_dialog_id=session_id,
                importance=m.get("importance", 3)
            )

        logger.info(f"成功写入 {len(memories)} 条长期记忆，user={user_id}")
        return {}

    except Exception as e:
        logger.error(f"记忆提取节点执行失败: {e}")
        # 失败时不影响主流程
        return {}
