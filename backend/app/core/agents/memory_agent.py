"""记忆提取 Agent - 从对话中提取用户长期记忆"""
import json
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger


class MemoryAgent:
    """记忆提取 Agent

    从用户和助手的对话中，自动提取需要长期记住的用户信息，
    包括用户偏好、个人特征、重要事实等。
    """

    def __init__(self, model: ChatOpenAI):
        self.model = model
        self.system_prompt = """你是一个专业的用户记忆提取器。

你的任务是分析用户和助手的对话，判断是否需要提取用户的长期记忆信息。

需要提取的信息类型：
1. **preference** - 用户偏好：如喜欢的技术栈、编程语言、工具等
2. **fact** - 个人事实：如学校、专业、职业、身份等
3. **insight** - 重要洞察：如项目需求、学习目标、工作计划等

提取规则：
- 只提取关于用户的信息，不要提取关于助手或通用知识的信息
- 每条记忆应该是一个独立的、完整的事实陈述
- 避免提取临时性的、一次性的信息（如"帮我查个天气"）
- 避免提取过于宽泛的信息（如"用户在聊天"）
- 优先提取可能在未来对话中有用的信息

你必须严格按以下 JSON 格式返回，不要返回其他内容：
```json
{
    "should_save": true/false,
    "memories": [
        {"content": "用户是湖北大学计算机专业学生", "type": "fact"},
        {"content": "用户偏好使用Python编程", "type": "preference"}
    ]
}
```

如果没有需要提取的信息，返回：
```json
{
    "should_save": false,
    "memories": []
}
```"""

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

            response = await self.model.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt)
            ])

            result_text = response.content.strip()

            # 尝试从返回文本中提取 JSON
            result = self._parse_json(result_text)

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
                if content and mem_type in ("preference", "fact", "insight"):
                    valid_memories.append({"content": content, "type": mem_type})

            if valid_memories:
                logger.info(f"提取到 {len(valid_memories)} 条用户记忆")
                return valid_memories

            return None

        except Exception as e:
            logger.error(f"记忆提取失败: {e}")
            return None

    def _parse_json(self, text: str) -> Optional[Dict]:
        """从文本中解析 JSON

        支持纯 JSON 和被 ```json ``` 包裹的格式

        Args:
            text: 待解析的文本

        Returns:
            解析后的字典，失败返回 None
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 中的内容
        import re
        pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试找到第一个 { 和最后一个 } 之间的内容
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None
