"""文本处理工具函数"""
import json
import re
from typing import Optional, Dict


def parse_json(text: str) -> Optional[Dict]:
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
