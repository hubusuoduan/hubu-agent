"""Skill 加载工具"""
import os
import re
from pathlib import Path

from langchain_core.tools import tool
from loguru import logger

from app.config import settings


# ── 系统 Skills 目录 ──
SYSTEM_SKILLS_DIR: Path = settings.skills_base_path

# ── 系统 Skill 注册表（启动时扫描，增删后刷新） ──
SKILL_REGISTRY: dict[str, str] = {}


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 SKILL.md 的 YAML frontmatter，返回 (meta_dict, body)"""
    meta: dict = {}
    if not content.startswith("---"):
        return meta, content

    end = content.find("---", 3)
    if end == -1:
        return meta, content

    fm = content[3:end].strip()
    body = content[end + 3:].strip()

    for line in fm.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            meta[key] = val

    return meta, body


def _scan_dir(skills_dir: Path) -> dict[str, str]:
    """扫描指定目录下的所有 Skill，返回 {name: description}"""
    registry: dict[str, str] = {}
    if not skills_dir or not skills_dir.exists():
        return registry

    for d in skills_dir.iterdir():
        if not d.is_dir():
            continue
        md_path = d / "SKILL.md"
        if not md_path.exists():
            continue
        try:
            content = md_path.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(content)
            name = meta.get("name", d.name)
            description = meta.get("description", "")
            # fallback: 从 body 第一行 # 标题提取描述
            if not description:
                for line in body.splitlines():
                    line = line.strip()
                    if line.startswith("#"):
                        description = line.lstrip("# ").strip()
                        break
            registry[name] = description
        except Exception:
            pass

    return registry


def _scan_skills(user_id: int | None = None) -> dict[str, str]:
    """合并系统 + 用户 Skill 注册表，返回 {name: description}"""
    # 系统级
    registry = dict(_scan_dir(SYSTEM_SKILLS_DIR))
    # 用户级（覆盖同名）
    if user_id:
        user_dir = settings.skills_path(user_id)
        registry.update(_scan_dir(user_dir))
    return registry


# 启动时初始化系统注册表
SKILL_REGISTRY.update(_scan_dir(SYSTEM_SKILLS_DIR))


def _skills_dirs() -> list[Path]:
    """获取当前用户的 Skills 目录列表（用户目录 + 系统目录）"""
    from app.callbacks import current_skills_dir
    sd = current_skills_dir.get("")
    if not sd:
        return [settings.skills_base_path]
    # os.pathsep 分隔的多路径（Windows: ; Linux: :）
    return [Path(p) for p in sd.split(os.pathsep) if p]


@tool(parse_docstring=True)
async def list_skills() -> str:
    """列出所有可用的 Skill。

    Returns:
        str: Skill 列表
    """
    try:
        skills_dirs = _skills_dirs()
        # 合并所有目录下的 Skill（用户目录优先，同名覆盖系统目录）
        seen: dict[str, Path] = {}
        for skills_dir in skills_dirs:
            if not skills_dir.exists():
                continue
            for d in skills_dir.iterdir():
                if d.is_dir() and (d / "SKILL.md").exists():
                    seen[d.name] = d

        if not seen:
            return "📭 暂无 Skill"

        lines = []
        for name in sorted(seen.keys(), key=str.lower):
            s = seen[name]
            desc = ""
            try:
                first_line = (s / "SKILL.md").read_text(encoding="utf-8").split("\n")[0].strip()
                if first_line.startswith("#"):
                    desc = first_line.lstrip("# ").strip()
            except Exception:
                pass
            lines.append(f"📦 {name}" + (f" - {desc}" if desc else ""))

        return "\n".join(lines)
    except Exception as e:
        return f"❌ 获取列表失败: {e}"


@tool(parse_docstring=True)
async def load_skill(skill_name: str) -> str:
    """加载指定 Skill 的 SKILL.md 内容。

    Args:
        skill_name: Skill 名称

    Returns:
        str: SKILL.md 内容
    """
    try:
        # 在所有 Skills 目录中查找（用户目录优先）
        for skills_dir in _skills_dirs():
            skill_dir = skills_dir / skill_name
            md_path = skill_dir / "SKILL.md"
            if md_path.exists():
                return md_path.read_text(encoding="utf-8")

        return f"❌ Skill 不存在: {skill_name}"
    except Exception as e:
        return f"❌ 加载失败: {e}"


@tool(parse_docstring=True)
async def list_skill_resources(skill_name: str) -> str:
    """列出指定 Skill 目录下的资源文件。

    Args:
        skill_name: Skill 名称

    Returns:
        str: 资源文件列表
    """
    try:
        # 在所有 Skills 目录中查找（用户目录优先）
        skill_dir = None
        for sd in _skills_dirs():
            candidate = sd / skill_name
            if candidate.exists():
                skill_dir = candidate
                break
        if not skill_dir:
            return f"❌ Skill 不存在: {skill_name}"

        items = []
        for item in sorted(skill_dir.rglob("*")):
            if item.is_file() and item.name != "SKILL.md":
                rel = item.relative_to(skill_dir)
                items.append(f"📄 {rel}")

        if not items:
            return "📭 该 Skill 下暂无资源文件"

        return "\n".join(items)
    except Exception as e:
        return f"❌ 获取列表失败: {e}"


@tool(parse_docstring=True)
async def read_skill_resource(skill_name: str, resource_path: str) -> str:
    """读取 Skill 下的资源文件内容。

    Args:
        skill_name: Skill 名称
        resource_path: 资源文件相对路径

    Returns:
        str: 文件内容
    """
    try:
        # 在所有 Skills 目录中查找（用户目录优先）
        skill_dir = None
        for sd in _skills_dirs():
            candidate = sd / skill_name
            if candidate.exists():
                skill_dir = candidate
                break
        if not skill_dir:
            return f"❌ Skill 不存在: {skill_name}"

        file_path = skill_dir / resource_path

        # 安全检查：防止路径穿越
        try:
            file_path.resolve().relative_to(skill_dir.resolve())
        except ValueError:
            return "❌ 非法路径"

        if not file_path.exists():
            return f"❌ 文件不存在: {resource_path}"

        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            data = file_path.read_bytes()
            size = len(data)
            if size > settings.FILE_MAX_SIZE:
                return f"❌ 文件过大 ({size} 字节)"
            return f"(二进制文件，{size} 字节，十六进制前100字节):\n{data[:100].hex()}"
    except Exception as e:
        return f"❌ 读取失败: {e}"
