"""提示词管理模块 - 从文件加载提示词"""
import os
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent

# 缓存已加载的提示词
_cache: dict[str, str] = {}


def load_prompt(name: str) -> str:
    """加载提示词文件

    Args:
        name: 提示词名称（不含扩展名），如 'chat_agent'、'memory_agent'

    Returns:
        提示词文本内容
    """
    if name in _cache:
        return _cache[name]

    file_path = _PROMPTS_DIR / f"{name}.md"
    if not file_path.exists():
        raise FileNotFoundError(f"提示词文件不存在: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    _cache[name] = content
    return content


def clear_cache() -> None:
    """清除提示词缓存（开发调试用）"""
    _cache.clear()
