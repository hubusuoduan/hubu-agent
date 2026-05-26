"""Skill加载工具 - 按需加载专业能力模块

设计原则：
- SKILL_REGISTRY 由扫描 skills/ 目录动态构建，不硬编码
- 三层渐进式加载，节省 token：
  第1层 load_skill(name) → 只返回 name + description
  第2层 load_skill(name, detail=True) → 返回 SKILL.md 完整指令
  第3层 read_skill_resource(name, path) → 读取具体子资源文件
- list_skill_resources(name) 按需查看资源文件列表
"""
import re
from pathlib import Path
from loguru import logger
from langchain.tools import tool

# Skills 根目录: action.py -> skill_loader -> tools -> app -> skills
SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 SKILL.md 的 YAML frontmatter，返回 (metadata, body)"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    meta = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"').strip("'")
    body = match.group(2).strip()
    return meta, body


def _scan_skills() -> dict[str, str]:
    """扫描 skills/ 目录，从每个 SKILL.md 的 frontmatter 读取 name 和 description，
    构建注册表 {name: description}。目录名作为 fallback name。"""
    registry: dict[str, str] = {}
    if not SKILLS_DIR.exists():
        logger.warning(f"Skills 目录不存在: {SKILLS_DIR}")
        return registry

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            content = skill_md.read_text(encoding="utf-8")
            meta, _ = _parse_frontmatter(content)
            name = meta.get("name", skill_dir.name)
            description = meta.get("description", "")
            registry[name] = description
        except Exception as e:
            logger.warning(f"扫描 Skill '{skill_dir.name}' 失败: {e}")
            registry[skill_dir.name] = ""

    return registry


# 启动时动态构建注册表
SKILL_REGISTRY: dict[str, str] = _scan_skills()


def _get_skill_dir(skill_name: str) -> Path:
    """获取 skill 目录路径（按目录名查找）"""
    return SKILLS_DIR / skill_name


def _list_resources(skill_name: str) -> list[str]:
    """列出 skill 目录下所有可读取的资源文件（相对路径）"""
    skill_dir = _get_skill_dir(skill_name)
    if not skill_dir.exists():
        return []

    # 二进制文件扩展名，不列出
    binary_exts = {
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
        ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc",
        ".zip", ".tar", ".gz", ".exe", ".dll", ".so",
    }

    resources = []
    for f in skill_dir.rglob("*"):
        if not f.is_file():
            continue
        if f.name in ("SKILL.md", "LICENSE.txt"):
            continue
        if f.suffix.lower() in binary_exts:
            continue
        rel = f.relative_to(skill_dir).as_posix()
        resources.append(rel)

    return sorted(resources)


def _build_skill_list_text() -> str:
    """构建可用 Skill 列表文本，用于工具描述和错误提示"""
    lines = []
    for name, desc in SKILL_REGISTRY.items():
        if desc:
            lines.append(f"- {name}: {desc}")
        else:
            lines.append(f"- {name}")
    return "\n".join(lines)


@tool(parse_docstring=True)
async def list_skills() -> str:
    """列出所有可用的 Skill 名称和描述。在不确定有哪些技能可用时，先调用此工具查看列表。
    确认需要的技能后，再调用 load_skill(skill_name, detail=True) 获取完整指令。

    Returns:
        str: 所有可用 Skill 的名称和描述列表
    """
    if not SKILL_REGISTRY:
        return "当前没有可用的 Skill"
    return "可用 Skill 列表:\n" + _build_skill_list_text()


@tool(parse_docstring=True)
async def load_skill(skill_name: str, detail: bool = False) -> str:
    """
    加载专业能力模块。首次调用只返回 Skill 的名称和描述，用于判断是否需要该能力；
    确认需要后，传入 detail=true 可获取完整指令内容。

    Args:
        skill_name: 要加载的 Skill 名称
        detail: 是否返回完整指令内容，默认 False 只返回名称和描述

    Returns:
        str: Skill 的名称和描述（detail=True 时返回完整指令）
    """
    return await _load_skill(skill_name, detail=detail)


@tool(parse_docstring=True)
async def list_skill_resources(skill_name: str) -> str:
    """
    列出 Skill 目录下所有可读取的资源文件（如参考文档、模板、脚本等）。
    在 load_skill 加载后，如需查看有哪些子资源文件时调用。

    Args:
        skill_name: Skill 名称

    Returns:
        str: 资源文件列表
    """
    if skill_name not in SKILL_REGISTRY:
        available = _build_skill_list_text()
        return f"Skill '{skill_name}' 不存在。\n可用 Skill:\n{available}"

    resources = _list_resources(skill_name)
    if not resources:
        return f"Skill '{skill_name}' 没有可用的资源文件"

    lines = [f"📂 {skill_name} 可用资源文件（使用 read_skill_resource 读取）:"]
    for r in resources:
        lines.append(f"  - {r}")
    return "\n".join(lines)


@tool(parse_docstring=True)
async def read_skill_resource(skill_name: str, resource_path: str) -> str:
    """
    读取 Skill 的子资源文件（如参考文档、模板、脚本等）。仅在 load_skill 加载后需要深入查看时使用。

    Args:
        skill_name: Skill 名称
        resource_path: 资源文件在 Skill 目录下的相对路径（如 "reference/models.md"、"scripts/example.py"）

    Returns:
        str: 资源文件的内容
    """
    return await _read_resource(skill_name, resource_path)


async def _load_skill(skill_name: str, detail: bool = False) -> str:
    """加载 Skill 信息。detail=False 只返回名称+描述，detail=True 返回完整指令。"""
    # 校验 skill_name 是否在注册表中
    if skill_name not in SKILL_REGISTRY:
        available = _build_skill_list_text()
        return f"Skill '{skill_name}' 不存在。\n可用 Skill:\n{available}"

    skill_dir = _get_skill_dir(skill_name)
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return f"Skill '{skill_name}' 已注册但 SKILL.md 文件缺失"

    try:
        content = skill_md.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)

        header = f"\U0001f527 Skill: {meta.get('name', skill_name)}"
        if meta.get("description"):
            header += f"\n\U0001f4dd 描述: {meta['description']}"

        if not detail:
            # 轻量模式：只返回 name + description，不列资源文件（节省 token）
            parts = [header]
            parts.append("")
            parts.append("\U0001f4a1 如需完整指令，调用 load_skill 并设置 detail=true")
            parts.append("\U0001f4a1 如需查看资源文件列表，调用 list_skill_resources")
            return "\n".join(parts)

        # 详细模式：返回完整指令，不列资源文件（按需用 list_skill_resources 查看）
        separator = "\u2500" * 40
        return "\n".join([header, separator, body])

    except Exception as e:
        logger.error(f"加载 Skill '{skill_name}' 失败: {e}")
        return f"加载 Skill '{skill_name}' 失败: {str(e)}"


async def _read_resource(skill_name: str, resource_path: str) -> str:
    """读取 Skill 的子资源文件"""
    # 校验 skill_name
    if skill_name not in SKILL_REGISTRY:
        available = _build_skill_list_text()
        return f"Skill '{skill_name}' 不存在。\n可用 Skill:\n{available}"

    skill_dir = _get_skill_dir(skill_name)
    file_path = skill_dir / resource_path

    # 安全检查：确保路径在 skill 目录内
    try:
        file_path.resolve().relative_to(skill_dir.resolve())
    except ValueError:
        return f"非法路径: '{resource_path}'，资源文件必须在 Skill 目录内"

    if not file_path.exists():
        resources = _list_resources(skill_name)
        available = "\n".join(f"  - {r}" for r in resources) if resources else "  （无可用资源）"
        return f"资源文件 '{resource_path}' 不存在。\n可用资源:\n{available}"

    if not file_path.is_file():
        return f"'{resource_path}' 不是一个文件"

    try:
        # 只读取文本文件，跳过二进制文件
        suffix = file_path.suffix.lower()
        binary_exts = {".ttf", ".otf", ".woff", ".woff2", ".eot", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc"}
        if suffix in binary_exts:
            return f"'{resource_path}' 是二进制文件（{suffix}），无法以文本形式读取"

        content = file_path.read_text(encoding="utf-8")
        header = f"\U0001f4c4 {skill_name}/{resource_path}"
        separator = "\u2500" * 40
        return f"{header}\n{separator}\n\n{content}"

    except UnicodeDecodeError:
        return f"'{resource_path}' 是二进制文件，无法以文本形式读取"
    except Exception as e:
        logger.error(f"读取资源文件 '{skill_name}/{resource_path}' 失败: {e}")
        return f"读取资源文件失败: {str(e)}"
