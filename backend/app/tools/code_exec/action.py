"""代码执行器 - 在完整Python环境中执行代码并返回结果

代码在工作区目录中执行，可通过环境变量感知路径：
- WORKSPACE_DIR: 工作区绝对路径（文件读写的根目录）
- SKILLS_DIR: Skill脚本根目录
"""
import sys
import tempfile
import os
import asyncio
import subprocess
import time
from pathlib import Path
from loguru import logger
from langchain.tools import tool

from app.config import settings

# 默认执行超时时间（秒）- 从配置读取
DEFAULT_TIMEOUT = settings.CODE_EXEC_TIMEOUT

# 代码执行的工作目录（与 file_manager 共享同一个工作区）
WORKSPACE_DIR = str(settings.file_workspace_path)

# Skills 根目录
SKILLS_DIR = str(Path(__file__).resolve().parent.parent.parent / "skills")

# 最大超时时间（秒）
MAX_TIMEOUT = settings.CODE_EXEC_MAX_TIMEOUT

# 最大输出字符数
MAX_OUTPUT_LENGTH = settings.CODE_EXEC_MAX_OUTPUT


@tool(parse_docstring=True)
async def code_exec(code: str, timeout: int = 60) -> str:
    """
    在完整Python环境中执行代码并返回输出结果。当你需要使用os、sys、io、pathlib等模块执行文件操作、系统调用等任务时调用此工具。

    支持所有已安装的Python库和系统模块，代码在独立子进程中运行，有超时保护但无模块限制。
    适用于需要执行复杂代码的场景（如文档处理、文件操作、数据分析等）。

    代码在工作区目录中执行，可通过以下环境变量感知路径：
    - os.environ["WORKSPACE_DIR"]: 工作区绝对路径，所有文件读写应基于此路径
    - os.environ["SKILLS_DIR"]: Skill脚本根目录

    Args:
        code (str): 要执行的Python代码
        timeout (int): 执行超时时间（秒），默认60秒，最大300秒

    Returns:
        str: 代码执行结果，包含输出、错误信息和执行耗时

    Examples:
        - Skill需要操作文件系统 -> code="import os; print(os.listdir('.'))"
        - Skill需要读写Excel -> code="import openpyxl; ..."
        - Skill需要执行脚本 -> 直接调用
    """
    return await _run_code(code, timeout)


def _snapshot_workspace(workspace: Path) -> set[str]:
    """扫描工作区，返回所有文件的相对路径集合"""
    files = set()
    if not workspace.exists():
        return files
    for f in workspace.rglob("*"):
        if f.is_file():
            files.add(str(f.relative_to(workspace)))
    return files


async def _run_code(code: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """执行Python代码"""

    # 参数校验
    if not code or not code.strip():
        return "❌ 代码内容不能为空"

    code = code.strip()

    # 限制超时时间
    if timeout <= 0:
        timeout = DEFAULT_TIMEOUT
    elif timeout > MAX_TIMEOUT:
        timeout = MAX_TIMEOUT
        logger.warning(f"timeout超过最大值{MAX_TIMEOUT}秒，已自动调整")

    try:
        # 执行前快照：记录工作区已有文件
        workspace = Path(WORKSPACE_DIR)
        before_files = _snapshot_workspace(workspace)

        result = await _execute_in_subprocess(code, timeout)

        # 执行后对比：检测新生成的文件
        after_files = _snapshot_workspace(workspace)
        new_files = after_files - before_files
        if new_files:
            new_files_sorted = sorted(new_files)
            files_info = "\n".join(f"  - {f}" for f in new_files_sorted)
            result += f"\n📁 本次执行新生成的文件:\n{files_info}"

        return result
    except Exception as e:
        error_msg = str(e) or repr(e) or type(e).__name__
        logger.error(f"代码执行器错误: {error_msg}", exc_info=True)
        return f"❌ 代码执行失败: {error_msg}"


def _run_subprocess_sync(code: str, timeout: int) -> tuple:
    """同步执行子进程（在线程中运行）"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        start_time = time.time()

        try:
            # 注入环境变量，让代码能感知工作区和Skill路径
            env = os.environ.copy()
            env["WORKSPACE_DIR"] = WORKSPACE_DIR
            env["SKILLS_DIR"] = SKILLS_DIR

            result = subprocess.run(
                [sys.executable, "-u", tmp_path],
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

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def _execute_in_subprocess(code: str, timeout: int) -> str:
    """在子进程中执行代码，使用完整环境"""
    stdout, stderr, returncode, elapsed, timed_out = await asyncio.to_thread(
        _run_subprocess_sync, code, timeout
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
        parts.append("📤 代码执行成功，无输出（如需查看结果，请使用 print() 输出）")

    return "\n\n".join(parts)
