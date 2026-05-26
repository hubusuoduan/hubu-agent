
"""文件管理器 - 在工作区内读写、列出、删除、移动文件和目录"""
import os
import shutil
import base64
from pathlib import Path
from datetime import datetime
from loguru import logger
from langchain.tools import tool

from app.config import settings
from app.utils.format import fmt_size


# ─── 安全校验 ───

def _resolve_path(path: str) -> Path:
    """将相对路径解析为工作区内的绝对路径，防止路径穿越"""
    workspace = settings.file_workspace_path
    # 清理路径，去除 .. 等穿越符号
    resolved = (workspace / path).resolve()
    # 确保解析后的路径仍在工作区内
    if not str(resolved).startswith(str(workspace.resolve())):
        raise ValueError(f"路径越权：'{path}' 超出工作区范围")
    return resolved


DENY_EXTENSIONS = {".exe", ".bat", ".cmd", ".ps1", ".sh", ".dll", ".so"}


def _check_extension(path: str) -> None:
    """检查文件扩展名是否被禁止"""
    ext = Path(path).suffix.lower()
    if ext in DENY_EXTENSIONS:
        raise ValueError(f"文件扩展名 '{ext}' 被禁止")


def _check_size(size: int) -> None:
    """检查文件大小是否超限"""
    if size > settings.FILE_MAX_SIZE:
        raise ValueError(f"文件大小 {size} 字节超过限制 {settings.FILE_MAX_SIZE} 字节")


# ─── 工具函数 ───


@tool(parse_docstring=True)
def file_write(path: str, content: str, encoding: str = "utf-8", mode: str = "write") -> str:
    """
    将文本内容写入工作区内的文件。如果文件所在目录不存在会自动创建。
    如果文件可能重名，建议在文件名中自行添加唯一标识。
    禁止的扩展名: .exe/.bat/.cmd/.ps1/.sh/.dll/.so，其他均可。

    Args:
        path (str): 相对于工作区的文件路径，如 'reports/summary.txt'
        content (str): 要写入的文本内容
        encoding (str): 文件编码，默认utf-8
        mode (str): 写入模式，'write'为覆盖写入，'append'为追加写入

    Returns:
        str: 操作结果，包含写入的文件路径和字节数
    """
    try:
        _check_extension(path)
        full_path = _resolve_path(path)
        _check_size(len(content.encode(encoding)))

        # 自动创建父目录
        full_path.parent.mkdir(parents=True, exist_ok=True)

        write_mode = "a" if mode == "append" else "w"
        with open(full_path, write_mode, encoding=encoding) as f:
            f.write(content)

        size = full_path.stat().st_size
        rel_path = full_path.relative_to(settings.file_workspace_path)
        return f"✅ 文件已写入: {rel_path} ({size} 字节)"
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_write 错误: {e}")
        return f"❌ 写入文件失败: {e}"


@tool(parse_docstring=True)
def file_write_bytes(path: str, content_base64: str) -> str:
    """
    将二进制内容（Base64编码）写入工作区内的文件。适用于图片、PDF、Excel等二进制文件。
    如果文件可能重名，建议在文件名中自行添加唯一标识。
    禁止的扩展名: .exe/.bat/.cmd/.ps1/.sh/.dll/.so，其他均可。

    Args:
        path (str): 相对于工作区的文件路径，如 'images/photo.png'
        content_base64 (str): Base64编码的文件内容

    Returns:
        str: 操作结果，包含写入的文件路径和字节数
    """
    try:
        _check_extension(path)
        raw = base64.b64decode(content_base64)
        _check_size(len(raw))

        full_path = _resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(raw)

        size = full_path.stat().st_size
        rel_path = full_path.relative_to(settings.file_workspace_path)
        return f"✅ 二进制文件已写入: {rel_path} ({size} 字节)"
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_write_bytes 错误: {e}")
        return f"❌ 写入二进制文件失败: {e}"


@tool(parse_docstring=True)
def file_read(path: str, encoding: str = "utf-8") -> str:
    """
    读取工作区内文本文件的内容。

    Args:
        path (str): 相对于工作区的文件路径
        encoding (str): 文件编码，默认utf-8

    Returns:
        str: 文件内容
    """
    try:
        full_path = _resolve_path(path)
        if not full_path.exists():
            return f"❌ 文件不存在: {path}"
        if full_path.is_dir():
            return f"❌ 路径是目录，不是文件: {path}"

        with open(full_path, "r", encoding=encoding) as f:
            content = f.read()

        return content
    except ValueError as e:
        return f"❌ {e}"
    except UnicodeDecodeError:
        return f"❌ 文件编码错误，可能不是文本文件，请使用 file_read_bytes"
    except Exception as e:
        logger.error(f"file_read 错误: {e}")
        return f"❌ 读取文件失败: {e}"


@tool(parse_docstring=True)
def file_read_bytes(path: str) -> str:
    """
    读取工作区内二进制文件的内容，返回Base64编码。适用于图片、PDF、Excel等文件。

    Args:
        path (str): 相对于工作区的文件路径

    Returns:
        str: Base64编码的文件内容
    """
    try:
        full_path = _resolve_path(path)
        if not full_path.exists():
            return f"❌ 文件不存在: {path}"

        with open(full_path, "rb") as f:
            raw = f.read()

        _check_size(len(raw))
        return base64.b64encode(raw).decode("ascii")
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_read_bytes 错误: {e}")
        return f"❌ 读取二进制文件失败: {e}"


@tool(parse_docstring=True)
def file_list(path: str = ".", pattern: str = "*", recursive: bool = False) -> str:
    """
    列出工作区内指定目录下的文件和子目录。

    Args:
        path (str): 相对于工作区的目录路径，默认为工作区根目录
        pattern (str): 文件名匹配模式，如 '*.txt'、'*.pdf'，默认'*'列出所有
        recursive (bool): 是否递归列出子目录内容，默认False

    Returns:
        str: 文件和目录列表，包含名称、类型、大小、修改时间
    """
    try:
        full_path = _resolve_path(path)
        if not full_path.exists():
            return f"❌ 目录不存在: {path}"
        if not full_path.is_dir():
            return f"❌ 路径不是目录: {path}"

        items = []
        if recursive:
            matches = full_path.rglob(pattern)
        else:
            matches = full_path.glob(pattern)

        workspace = settings.file_workspace_path
        for item in sorted(matches, key=lambda p: (not p.is_dir(), str(p).lower())):
            rel = item.relative_to(workspace)
            if item.is_dir():
                items.append(f"📁 {rel}/")
            else:
                size = item.stat().st_size
                mtime = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                items.append(f"📄 {rel}  ({fmt_size(size)}, {mtime})")

        if not items:
            return f"📭 目录为空: {path}"

        header = f"📂 {path} (共 {len(items)} 项)"
        return header + "\n" + "\n".join(items)
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_list 错误: {e}")
        return f"❌ 列出目录失败: {e}"


@tool(parse_docstring=True)
def file_delete(path: str) -> str:
    """
    删除工作区内的文件或目录（目录会递归删除）。

    Args:
        path (str): 相对于工作区的文件或目录路径

    Returns:
        str: 操作结果
    """
    try:
        full_path = _resolve_path(path)
        if not full_path.exists():
            return f"❌ 文件或目录不存在: {path}"

        if full_path.is_dir():
            shutil.rmtree(full_path)
            return f"✅ 目录已删除: {path}"
        else:
            full_path.unlink()
            return f"✅ 文件已删除: {path}"
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_delete 错误: {e}")
        return f"❌ 删除失败: {e}"


@tool(parse_docstring=True)
def file_move(src: str, dst: str) -> str:
    """
    移动或重命名工作区内的文件或目录。

    Args:
        src (str): 源路径（相对于工作区）
        dst (str): 目标路径（相对于工作区）

    Returns:
        str: 操作结果
    """
    try:
        _check_extension(dst)
        src_path = _resolve_path(src)
        dst_path = _resolve_path(dst)

        if not src_path.exists():
            return f"❌ 源文件不存在: {src}"

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        return f"✅ 已移动: {src} → {dst}"
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_move 错误: {e}")
        return f"❌ 移动失败: {e}"


@tool(parse_docstring=True)
def file_mkdir(path: str) -> str:
    """
    在工作区内创建目录（含父目录）。

    Args:
        path (str): 相对于工作区的目录路径

    Returns:
        str: 操作结果
    """
    try:
        full_path = _resolve_path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        return f"✅ 目录已创建: {path}"
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_mkdir 错误: {e}")
        return f"❌ 创建目录失败: {e}"


@tool(parse_docstring=True)
def file_exists(path: str) -> str:
    """
    检查工作区内文件或目录是否存在。

    Args:
        path (str): 相对于工作区的路径

    Returns:
        str: 存在则返回类型和大小信息，不存在则提示
    """
    try:
        full_path = _resolve_path(path)
        if not full_path.exists():
            return f"❌ 不存在: {path}"
        if full_path.is_dir():
            return f"📁 目录存在: {path}"
        size = full_path.stat().st_size
        return f"📄 文件存在: {path} ({fmt_size(size)})"
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_exists 错误: {e}")
        return f"❌ 检查失败: {e}"


@tool(parse_docstring=True)
def file_info(path: str) -> str:
    """
    获取工作区内文件或目录的详细信息（大小、修改时间、权限等）。

    Args:
        path (str): 相对于工作区的路径

    Returns:
        str: 文件详细信息
    """
    try:
        full_path = _resolve_path(path)
        if not full_path.exists():
            return f"❌ 文件或目录不存在: {path}"

        stat = full_path.stat()
        info_lines = [
            f"📌 路径: {path}",
            f"📂 类型: {'目录' if full_path.is_dir() else '文件'}",
            f"📏 大小: {fmt_size(stat.st_size)}",
            f"🕐 创建时间: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"✏️ 修改时间: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if full_path.is_file():
            info_lines.append(f"📎 扩展名: {full_path.suffix}")

        return "\n".join(info_lines)
    except ValueError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"file_info 错误: {e}")
        return f"❌ 获取信息失败: {e}"


# ─── 辅助函数 ───

def fmt_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}" if unit != "B" else f"{size}{unit}"
        size /= 1024
    return f"{size:.1f}TB"
