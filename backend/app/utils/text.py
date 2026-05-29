"""文本处理工具函数"""
import json
import re
from typing import Optional, Dict, List


def truncate(text: str, max_len: int = 1000, suffix: str = "...") -> str:
    """截断文本到指定长度

    统一的文本截断工具，消除散落在各处的 text[:N] + "..." 模式。

    Args:
        text: 原始文本
        max_len: 最大字符数
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if not text:
        return text
    if len(text) <= max_len:
        return text
    return text[:max_len] + suffix


def format_scratchpad(
    scratchpad: List[dict],
    max_output: int = 500,
    prefix: str = "- ",
    separator: str = "\n",
    fmt: str = "{prefix}{name}: {output}",
) -> str:
    """格式化 Agent 执行记录（agent_scratchpad）

    将 scratchpad 列表格式化为可读的文本，用于 Supervisor/Reviewer 的
    提示词构建。消除 supervisor_agent、reviewer_agent、base_react_agent
    中的重复格式化逻辑。

    Args:
        scratchpad: Agent 执行记录列表，格式: [{"agent": "xxx", "output": "..."}]
        max_output: 每条输出的最大字符数
        prefix: 每条记录的前缀
        separator: 记录之间的分隔符
        fmt: 单条记录的格式模板，可用变量: {prefix}, {name}, {output}

    Returns:
        格式化后的文本，如: "- researcher: 搜索结果...\n- coder: 代码输出..."
    """
    if not scratchpad:
        return ""
    lines = []
    for item in scratchpad:
        agent_name = item.get("agent", "unknown")
        output = truncate(item.get("output", ""), max_output)
        lines.append(fmt.format(prefix=prefix, name=agent_name, output=output))
    return separator.join(lines)


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
