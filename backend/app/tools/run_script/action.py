"""Skill脚本执行器 - 在工作区中执行Skill目录下的脚本

解决 SKILL.md 中引用脚本（如 python scripts/office/unpack.py）时路径不对的问题。
自动将 Skill 脚本路径解析为绝对路径，cwd 设为工作区目录。
"""
import sys
import os
import asyncio
import subprocess
import time
from pathlib import Path
from loguru import logger
from langchain.tools import tool

from app.config import settings

# Skills 根目录
SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"

# 工作区目录
WORKSPACE_DIR = str(settings.file_workspace_path)

# 默认超时时间（秒）
DEFAULT_TIMEOUT = settings.CODE_EXEC_TIMEOUT

# 最大超时时间（秒）
MAX_TIMEOUT = settings.CODE_EXEC_MAX_TIMEOUT

# 最大输出字符数
MAX_OUTPUT_LENGTH = settings.CODE_EXEC_MAX_OUTPUT


def _resolve_script_path(skill_name: str, script_path: str) -> Path:
    """将 Skill 内的相对脚本路径解析为绝对路径

    Args:
        skill_name: Skill 名称（如 docx, pdf, pptx）
        script_path: 脚本在 Skill 目录下的相对路径（如 scripts/office/unpack.py）

    Returns:
        脚本的绝对路径
    """
    skill_dir = SKILLS_DIR / skill_name
    if not skill_dir.exists():
        raise ValueError(f"Skill '{skill_name}' 不存在")

    full_path = skill_dir / script_path

    # 安全检查：确保路径在 Skill 目录内
    try:
        full_path.resolve().relative_to(skill_dir.resolve())
    except ValueError:
        raise ValueError(f"非法路径: '{script_path}'，脚本必须在 Skill 目录内")

    if not full_path.exists():
        raise ValueError(f"脚本不存在: {skill_name}/{script_path}")

    if not full_path.is_file():
        raise ValueError(f"'{script_path}' 不是文件")

    return full_path.resolve()


@tool(parse_docstring=True)
async def run_script(skill_name: str, script_path: str, args: str = "", timeout: int = 60) -> str:
    """
    执行Skill目录下的Python脚本。当SKILL.md指引你运行 python scripts/xxx.py 时，使用此工具代替直接调用code_exec。

    此工具会自动将脚本路径解析为Skill目录下的绝对路径，并在工作区目录中执行。
    适用于文档处理脚本（如 unpack.py、pack.py、validate.py、thumbnail.py 等）。

    Args:
        skill_name (str): Skill名称，如 docx、pdf、pptx、xlsx
        script_path (str): 脚本在Skill目录下的相对路径，如 scripts/office/unpack.py
        args (str): 传递给脚本的命令行参数，多个参数用空格分隔，如 "document.docx unpacked/"
        timeout (int): 执行超时时间（秒），默认60秒，最大300秒

    Returns:
        str: 脚本执行结果，包含输出、错误信息和执行耗时

    Examples:
        - SKILL.md说运行 "python scripts/office/unpack.py document.docx unpacked/" -> skill_name="docx", script_path="scripts/office/unpack.py", args="document.docx unpacked/"
        - SKILL.md说运行 "python scripts/office/validate.py doc.docx" -> skill_name="docx", script_path="scripts/office/validate.py", args="doc.docx"
    """
    return await _run_script(skill_name, script_path, args, timeout)


async def _run_script(skill_name: str, script_path: str, args: str, timeout: int) -> str:
    """执行Skill脚本"""

    # 限制超时时间
    if timeout <= 0:
        timeout = DEFAULT_TIMEOUT
    elif timeout > MAX_TIMEOUT:
        timeout = MAX_TIMEOUT
        logger.warning(f"timeout超过最大值{MAX_TIMEOUT}秒，已自动调整")

    try:
        script_full_path = _resolve_script_path(skill_name, script_path)
    except ValueError as e:
        return f"❌ {e}"

    try:
        result = await _execute_script(script_full_path, args, timeout)
        return result
    except Exception as e:
        error_msg = str(e) or repr(e) or type(e).__name__
        logger.error(f"Skill脚本执行错误: {error_msg}", exc_info=True)
        return f"❌ 脚本执行失败: {error_msg}"


def _run_script_sync(script_path: Path, args: str, timeout: int) -> tuple:
    """同步执行脚本（在线程中运行）"""
    start_time = time.time()

    # 构建命令
    cmd = [sys.executable, "-u", str(script_path)]
    if args and args.strip():
        cmd.extend(args.strip().split())

    # 将 Skill 的 scripts 目录加入 PYTHONPATH，以便脚本内部 import
    env = os.environ.copy()
    skill_scripts_dir = str(script_path.parent)
    # 也把 Skill 根目录加入，方便脚本 import 同级模块
    skill_root = str(script_path.parent.parent)
    existing_pythonpath = env.get("PYTHONPATH", "")
    extra_paths = f"{skill_root}{os.pathsep}{skill_scripts_dir}"
    env["PYTHONPATH"] = f"{extra_paths}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else extra_paths

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR,
            env=env,
        )
        timed_out = False
        stdout_bytes = result.stdout
        stderr_bytes = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        stdout_bytes = b""
        stderr_bytes = f"执行超时（{timeout}秒），进程已终止".encode("utf-8")
        returncode = -1

    elapsed = round(time.time() - start_time, 2)

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    return stdout, stderr, returncode, elapsed, timed_out


async def _execute_script(script_path: Path, args: str, timeout: int) -> str:
    """在子进程中执行Skill脚本"""
    stdout, stderr, returncode, elapsed, timed_out = await asyncio.to_thread(
        _run_script_sync, script_path, args, timeout
    )
    return _format_result(stdout, stderr, returncode, elapsed, timeout, timed_out)


def _format_result(
    stdout: str,
    stderr: str,
    returncode: int,
    elapsed: float,
    timeout: int,
    timed_out: bool,
) -> str:
    """格式化执行结果"""
    parts = []
    parts.append(f"⏱ 执行耗时: {elapsed}秒")

    if timed_out:
        parts.append(f"⚠️ 执行超时（限制{timeout}秒），请优化代码或增加超时时间")

    if returncode != 0 and not timed_out:
        parts.append(f"❌ 退出码: {returncode}")

    # 标准输出
    if stdout.strip():
        output = stdout.strip()
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH]
            output += f"\n... (输出已截断，共 {len(stdout.strip())} 字符)"
        parts.append(f"📤 输出:\n{output}")

    # 标准错误
    if stderr.strip():
        error = stderr.strip()
        if len(error) > MAX_OUTPUT_LENGTH:
            error = error[:MAX_OUTPUT_LENGTH]
            error += "\n... (错误信息已截断)"
        parts.append(f"🔴 错误:\n{error}")

    # 无输出
    if not stdout.strip() and not stderr.strip() and returncode == 0:
        parts.append("📤 脚本执行成功，无输出")

    return "\n\n".join(parts)
