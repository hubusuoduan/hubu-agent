"""AGENT.md 解析器 - 读取用户自建 Agent 的配置文件

AGENT.md 格式:
    ---
    name: translator
    display_name: 翻译官
    description: 擅长中英互译，保持原文语义和风格
    tools: [web_search, knowledge_search]
    ---

    你是一个专业翻译官，擅长中英互译。
    ...（system_prompt 正文）

YAML 元数据头（--- 包裹）包含结构化配置，
之后的 Markdown 正文即为 system_prompt。
"""
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from loguru import logger

from app.tools import AgentToolsWithName


@dataclass
class AgentConfig:
    """用户自建 Agent 配置（从 AGENT.md 解析而来）"""
    name: str                           # Agent 名称，如 "translator"
    display_name: str                   # 显示名，如 "翻译官"
    description: str                    # 简短描述，给 Supervisor 路由用
    tools: List[str] = field(default_factory=list)  # 工具名称列表
    system_prompt: str = ""             # system_prompt 正文

    @property
    def resolved_tools(self) -> list:
        """从工具池解析出实际的工具实例列表"""
        return [AgentToolsWithName[t] for t in self.tools if t in AgentToolsWithName]

    @property
    def node_name(self) -> str:
        """图中的节点名（加 user_ 前缀避免和系统 Agent 冲突）"""
        return f"user_{self.name}"


# AGENT.md 文件存放根目录
_CUSTOM_AGENTS_DIR = Path(__file__).parent


def _parse_yaml_header(content: str) -> tuple[dict, str]:
    """解析 AGENT.md 的 YAML 元数据头和正文

    Args:
        content: AGENT.md 文件内容

    Returns:
        (metadata_dict, prompt_body)
    """
    # 匹配 --- ... --- 包裹的 YAML 头
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        # 没有 YAML 头，整个内容作为 prompt
        logger.warning("AGENT.md 缺少 YAML 元数据头，将整个内容作为 system_prompt")
        return {}, content.strip()

    yaml_str = match.group(1)
    prompt_body = match.group(2).strip()

    # 简单解析 YAML（避免引入 pyyaml 依赖）
    metadata = {}
    for line in yaml_str.split("\n"):
        line = line.strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # 解析列表格式 [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip("'\"") for item in value[1:-1].split(",")]
            metadata[key] = [item for item in items if item]
        else:
            # 去除引号
            metadata[key] = value.strip("'\"")

    return metadata, prompt_body


def load_agent_config(agent_path: str) -> Optional[AgentConfig]:
    """解析 AGENT.md 文件，返回 AgentConfig

    Args:
        agent_path: 相对于 custom agents 目录的路径，如 "custom/1/translator/AGENT.md"
                    也支持绝对路径

    Returns:
        AgentConfig 或 None（文件不存在或解析失败）
    """
    # 尝试作为相对路径
    path = Path(agent_path)
    if not path.is_absolute():
        # agent_path 格式为 "custom/{user_id}/{name}/AGENT.md"
        # _CUSTOM_AGENTS_DIR 已经是 custom/ 目录，需要去掉前缀 "custom/"
        if agent_path.startswith("custom/"):
            path = _CUSTOM_AGENTS_DIR / agent_path[len("custom/"):]
        else:
            path = _CUSTOM_AGENTS_DIR / agent_path

    if not path.exists():
        logger.error(f"AGENT.md 文件不存在: {path}")
        return None

    try:
        content = path.read_text(encoding="utf-8")
        metadata, system_prompt = _parse_yaml_header(content)

        name = metadata.get("name", "")
        if not name:
            logger.error(f"AGENT.md 缺少 name 字段: {path}")
            return None

        config = AgentConfig(
            name=name,
            display_name=metadata.get("display_name", name),
            description=metadata.get("description", ""),
            tools=metadata.get("tools", []),
            system_prompt=system_prompt,
        )

        logger.info(f"解析 AGENT.md 成功: {config.name} ({config.display_name}), 工具: {config.tools}")
        return config

    except Exception as e:
        logger.error(f"解析 AGENT.md 失败: {path}, 错误: {e}")
        return None


def load_agent_configs(agent_records: list) -> List[AgentConfig]:
    """批量加载用户自建 Agent 配置

    Args:
        agent_records: UserAgentTable 记录列表（来自 DAO 层）

    Returns:
        成功解析的 AgentConfig 列表（跳过失败的）
    """
    configs = []
    for record in agent_records:
        config = load_agent_config(record.agent_path)
        if config:
            # 用数据库记录中的 description 覆盖（更可靠，避免每次读文件）
            if record.description:
                config.description = record.description
            if record.display_name:
                config.display_name = record.display_name
            configs.append(config)
        else:
            logger.warning(f"跳过无法解析的用户 Agent: {record.name}, path: {record.agent_path}")
    return configs
