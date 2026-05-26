"""记忆提取 Agent - 从对话中提取用户长期记忆"""
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from app.prompts import load_prompt
from app.utils.text import parse_json


class MemoryAgent:
    """记忆提取 Agent

    从用户和助手的对话中，自动提取需要长期记住的用户信息，
    包括用户偏好、个人特征、重要事实等。
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.system_prompt = load_prompt("memory_agent")

    async def extract(
        self,
        user_input: str,
        assistant_response: str,
        existing_memories: Optional[List[str]] = None
    ) -> Optional[List[Dict]]:
        """从一轮对话中提取用户记忆

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            existing_memories: 用户已有记忆内容列表，用于去重

        Returns:
            需要保存的记忆列表，每条包含 content 和 type；如果不需要保存则返回 None
        """
        try:
            # 构建已有记忆提示
            memory_hint = ""
            if existing_memories:
                memory_list = "\n".join(f"- {m}" for m in existing_memories)
                memory_hint = f"""

用户已有的记忆（请勿提取与已有记忆重复或高度相似的信息，如果新信息是对已有记忆的补充或更新，则仍然提取）：
{memory_list}"""

            user_prompt = f"""请分析以下对话，提取需要长期记住的用户信息：{memory_hint}

用户: {user_input}

助手: {assistant_response}

请返回 JSON 格式的结果。"""

            # 注入 Token 采集 Callback
            from app.callbacks import usage_metadata_callback
            response = await self.model.ainvoke(
                [SystemMessage(content=self.system_prompt),
                 HumanMessage(content=user_prompt)],
                config={"callbacks": [usage_metadata_callback]}
            )

            result_text = response.content.strip()

            # 尝试从返回文本中提取 JSON
            result = parse_json(result_text)

            if result is None:
                logger.warning(f"记忆提取 JSON 解析失败: {result_text[:100]}")
                return None

            should_save = result.get("should_save", False)
            memories = result.get("memories", [])

            if not should_save or not memories:
                logger.info("本轮对话无需提取记忆")
                return None

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

            return None

        except Exception as e:
            logger.error(f"记忆提取失败: {e}")
            return None

