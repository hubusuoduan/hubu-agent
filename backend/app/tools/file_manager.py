"""文件管理工具"""
import os
import shutil
from pathlib import Path

from langchain_core.tools import tool
from loguru import logger

from app.config import settings


def _workspace() -> Path:
    """获取当前工作区路径"""
    from app.callbacks import current_workspace_dir
    ws = current_workspace_dir.get("")
    return Path(ws) if ws else settings.file_workspace_path()


@tool(parse_docstring=True)
async def file_write(path: str, content: str) -> str:
    """写入文本文件。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 文件路径
        content: 文件内容

    Returns:
        str: 操作结果
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"✅ 已写入 {target}"
    except Exception as e:
        return f"❌ 写入失败: {e}"


@tool(parse_docstring=True)
async def file_write_bytes(path: str, data_hex: str) -> str:
    """写入二进制文件。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 文件路径
        data_hex: 十六进制编码的二进制数据

    Returns:
        str: 操作结果
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bytes.fromhex(data_hex))
        return f"✅ 已写入 {target} ({len(bytes.fromhex(data_hex))} 字节)"
    except Exception as e:
        return f"❌ 写入失败: {e}"


@tool(parse_docstring=True)
async def file_read(path: str) -> str:
    """读取文本文件。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 文件路径

    Returns:
        str: 文件内容
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        if not target.exists():
            return f"❌ 文件不存在: {path}"
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "❌ 文件不是文本格式，请使用 file_read_bytes"
    except Exception as e:
        return f"❌ 读取失败: {e}"


@tool(parse_docstring=True)
async def file_read_bytes(path: str) -> str:
    """读取二进制文件并返回十六进制编码。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 文件路径

    Returns:
        str: 十六进制编码的文件内容
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        if not target.exists():
            return f"❌ 文件不存在: {path}"
        data = target.read_bytes()
        size = len(data)
        if size > settings.FILE_MAX_SIZE:
            return f"❌ 文件过大 ({size} 字节)，上限 {settings.FILE_MAX_SIZE} 字节"
        return data.hex()
    except Exception as e:
        return f"❌ 读取失败: {e}"


@tool(parse_docstring=True)
async def file_list(path: str = "") -> str:
    """列出目录内容。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 目录路径，留空列出工作区根目录

    Returns:
        str: 目录内容列表
    """
    try:
        target = Path(path) if path and Path(path).is_absolute() else _workspace() / path
        if not target.exists():
            return f"❌ 目录不存在: {path}"
        if not target.is_dir():
            return f"❌ 不是目录: {path}"

        items = sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        if not items:
            return "📭 空目录"

        lines = []
        for item in items:
            if item.is_dir():
                lines.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                lines.append(f"📄 {item.name} ({size} 字节)")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 列出失败: {e}"


@tool(parse_docstring=True)
async def file_delete(path: str) -> str:
    """删除文件或目录。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 文件或目录路径

    Returns:
        str: 操作结果
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        if not target.exists():
            return f"❌ 不存在: {path}"
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return f"✅ 已删除 {target}"
    except Exception as e:
        return f"❌ 删除失败: {e}"


@tool(parse_docstring=True)
async def file_move(src: str, dst: str) -> str:
    """移动或重命名文件/目录。路径相对于工作区，也可使用绝对路径。

    Args:
        src: 源路径
        dst: 目标路径

    Returns:
        str: 操作结果
    """
    try:
        src_path = Path(src) if Path(src).is_absolute() else _workspace() / src
        dst_path = Path(dst) if Path(dst).is_absolute() else _workspace() / dst
        if not src_path.exists():
            return f"❌ 源路径不存在: {src}"
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        return f"✅ 已移动 {src_path} → {dst_path}"
    except Exception as e:
        return f"❌ 移动失败: {e}"


@tool(parse_docstring=True)
async def file_mkdir(path: str) -> str:
    """创建目录。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 目录路径

    Returns:
        str: 操作结果
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        target.mkdir(parents=True, exist_ok=True)
        return f"✅ 已创建目录 {target}"
    except Exception as e:
        return f"❌ 创建失败: {e}"


@tool(parse_docstring=True)
async def file_exists(path: str) -> str:
    """检查文件或目录是否存在。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 文件或目录路径

    Returns:
        str: 存在状态
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        if not target.exists():
            return f"❌ 不存在: {path}"
        kind = "目录" if target.is_dir() else "文件"
        return f"✅ {kind}存在: {target}"
    except Exception as e:
        return f"❌ 检查失败: {e}"


@tool(parse_docstring=True)
async def file_info(path: str) -> str:
    """获取文件或目录信息。路径相对于工作区，也可使用绝对路径。

    Args:
        path: 文件或目录路径

    Returns:
        str: 文件信息
    """
    try:
        target = Path(path) if Path(path).is_absolute() else _workspace() / path
        if not target.exists():
            return f"❌ 不存在: {path}"
        stat = target.stat()
        kind = "目录" if target.is_dir() else "文件"
        size = stat.st_size
        import time
        mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
        return f"{kind}: {target}\n大小: {size} 字节\n修改时间: {mtime}"
    except Exception as e:
        return f"❌ 获取信息失败: {e}"
