"""Memory Extract Agent - 从对话中提取用户长期记忆"""
from loguru import logger

from app.core.agents.bases import BaseLLMAgent
from app.core.graph.state import ChatState
from app.utils.text import parse_json


class MemoryExtractAgent(BaseLLMAgent):
    """Memory Extract Agent - 从对话中提取用户长期记忆

    分析本轮对话，提取需要长期记住的用户信息。
    继承 BaseLLMAgent（单次 LLM 调用）。
    """

    name = "memory_extract"
    prompt_name = "memory_agent"

    @classmethod
    def _build_user_prompt(cls, state: ChatState, existing_memories: list = None) -> str:
        """构建用户提示词

        Args:
            state: Graph 状态
            existing_memories: 用户已有记忆列表（去重用）
        """
        user_input = state.get("user_input", "")
        response = state.get("response", "")
        existing_memories = existing_memories or []

        # 构建已有记忆提示
        memory_hint = ""
        if existing_memories:
            memory_list = "\n".join(f"- {m}" for m in existing_memories)
            memory_hint = f"""

用户已有的记忆（请勿提取与已有记忆重复或高度相似的信息，如果新信息是对已有记忆的补充或更新，则仍然提取）：
{memory_list}"""

        return f"""请分析以下对话，提取需要长期记住的用户信息：{memory_hint}

用户: {user_input}

助手: {response}

请返回 JSON 格式的结果。"""

    @classmethod
    async def extract(cls, state: ChatState, existing_memories: list = None) -> list:
        """执行记忆提取（纯 LLM 调用，不涉及存储）

        Args:
            state: Graph 状态
            existing_memories: 用户已有记忆列表（去重用）

        Returns:
            提取到的记忆列表 [{content, type, importance}]，无则返回空列表
        """
        try:
            user_prompt = cls._build_user_prompt(state, existing_memories=existing_memories)
            result_text = await cls.invoke_llm(user_prompt)

            # 解析结果
            result = parse_json(result_text)

            if result is None:
                logger.warning(f"记忆提取 JSON 解析失败: {result_text[:100]}")
                return []

            should_save = result.get("should_save", False)
            memories = result.get("memories", [])

            if not should_save or not memories:
                logger.info("本轮对话无需提取记忆")
                return []

            # 验证每条记忆的格式
            valid_memories = []
            for m in memories:
                content = m.get("content", "").strip()
                mem_type = m.get("type", "fact").strip()
                importance = m.get("importance", 3)
                if not isinstance(importance, int) or importance < 1 or importance > 5:
                    importance = 3
                if content and mem_type in ("preference", "fact", "insight"):
                    valid_memories.append({"content": content, "type": mem_type, "importance": importance})

            if valid_memories:
                logger.info(f"提取到 {len(valid_memories)} 条用户记忆")

            return valid_memories

        except Exception as e:
            logger.error(f"记忆提取失败: {e}")
            return []
