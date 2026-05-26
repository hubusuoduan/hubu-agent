"""沙箱代码执行器 - 在受限环境中安全执行用户代码"""
import sys
import io
import traceback
import time
import re
from contextlib import redirect_stdout, redirect_stderr
from loguru import logger
from langchain.tools import tool

from app.config import settings

# 默认执行超时时间（秒）- 从配置读取
DEFAULT_TIMEOUT = settings.SANDBOX_TIMEOUT

# 最大超时时间（秒）
MAX_TIMEOUT = settings.SANDBOX_MAX_TIMEOUT

# 最大输出字符数
MAX_OUTPUT_LENGTH = settings.SANDBOX_MAX_OUTPUT

# 禁止导入的危险模块
BLOCKED_MODULES = {
    "os", "subprocess", "shutil", "signal", "ctypes",
    "socket", "http", "urllib", "requests",
    "sys", "pathlib", "glob",
    "pickle", "shelve", "marshal",
    "multiprocessing", "threading", "concurrent",
    "importlib", "pkg_resources", "pip",
}

# 沙箱中允许的内置函数（移除危险项）
SAFE_BUILTINS = {
    k: v for k, v in __builtins__.items() if k not in {
        "__import__", "exec", "eval", "compile",
        "open", "input", "breakpoint",
        "globals", "locals", "vars",
        "dir", "getattr", "setattr", "delattr",
        "memoryview", "type",
    }
} if isinstance(__builtins__, dict) else {
    k: getattr(__builtins__, k) for k in dir(__builtins__) if k not in {
        "__import__", "exec", "eval", "compile",
        "open", "input", "breakpoint",
        "globals", "locals", "vars",
        "dir", "getattr", "setattr", "delattr",
        "memoryview", "type",
    } and not k.startswith("_")
}


def _make_safe_import():
    """创建受限的 __import__ 函数，禁止导入危险模块"""
    original_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def safe_import(name, *args, **kwargs):
        # 检查顶层模块名
        top_level = name.split(".")[0]
        if top_level in BLOCKED_MODULES:
            raise ImportError(
                f"沙箱限制：禁止导入模块 '{top_level}'。"
                f"如需使用完整Python环境，请使用 code_exec 工具。"
            )
        return original_import(name, *args, **kwargs)

    return safe_import


def _build_sandbox_globals() -> dict:
    """构建沙箱的全局命名空间"""
    safe_builtins = dict(SAFE_BUILTINS)
    safe_builtins["__import__"] = _make_safe_import()
    return {"__builtins__": safe_builtins}


@tool(parse_docstring=True)
async def code_runner(code: str, timeout: int = 30) -> str:
    """
    在沙箱环境中安全执行Python代码并返回输出结果。当需要运行简单代码来计算、处理数据、验证逻辑时调用此工具。

    代码在受限的沙箱环境中运行，禁止导入危险模块（如os、subprocess、socket等），
    禁止文件操作（open）和动态执行（exec/eval）。如果需要使用完整Python环境，请使用 code_exec 工具。

    Args:
        code (str): 要执行的Python代码
        timeout (int): 执行超时时间（秒），默认30秒，最大120秒

    Returns:
        str: 代码执行结果，包含输出、错误信息和执行耗时

    Examples:
        - "帮我算一下 2^10" -> code="print(2**10)"
        - "写个排序算法测试一下" -> 直接调用
    """
    return await _run_code(code, timeout)


async def _run_code(code: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """在沙箱中执行Python代码"""

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
        start_time = time.time()
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        sandbox_globals = _build_sandbox_globals()

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, sandbox_globals)

        elapsed = round(time.time() - start_time, 2)
        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()

        return _format_result(stdout, stderr, elapsed, timeout)

    except ImportError as e:
        # 沙箱限制触发的导入错误
        return f"⚠️ {str(e)}"
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        stderr = stderr_capture.getvalue()
        tb = traceback.format_exc()
        return _format_result(stdout_capture.getvalue(), stderr + "\n" + tb, elapsed, timeout)


def _format_result(
    stdout: str,
    stderr: str,
    elapsed: float,
    timeout: int,
) -> str:
    """格式化执行结果"""
    parts = []
    parts.append(f"⏱ 执行耗时: {elapsed}秒")

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
    if not stdout.strip() and not stderr.strip():
        parts.append("📤 代码执行成功，无输出（如需查看结果，请使用 print() 输出）")

    return "\n\n".join(parts)


