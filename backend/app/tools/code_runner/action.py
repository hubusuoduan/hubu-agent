"""沙箱代码执行器 - 安全执行Python代码并返回结果"""
import sys
import tempfile
import os
import json
import time
from loguru import logger
from langchain.tools import tool

from app.config import settings

# 默认执行超时时间（秒）
DEFAULT_TIMEOUT = 30

# 最大输出字符数
MAX_OUTPUT_LENGTH = 5000

# 禁止导入的危险模块（安全限制）
BLOCKED_MODULES = {
    "os", "subprocess", "shutil", "signal", "ctypes",
    "socket", "http", "urllib", "requests",
    "sys", "pathlib", "glob", "io",
    "pickle", "shelve", "marshal",
    "multiprocessing", "threading", "concurrent",
    "importlib", "pkg_resources", "pip",
}


@tool(parse_docstring=True)
async def code_runner(code: str, timeout: int = 30) -> str:
    """
    在沙箱环境中执行Python代码并返回输出结果。当需要运行代码来计算、处理数据、验证逻辑或调试时调用此工具。代码在受限的子进程中运行，支持标准输出和标准错误捕获。

    Args:
        code (str): 要执行的Python代码。
        timeout (int): 执行超时时间（秒），默认30秒，最大120秒。

    Returns:
        str: 代码执行结果，包含标准输出、标准错误和退出码。如果代码出错，会包含错误信息以便自我修正。

    Examples:
        - "帮我算一下 2^10" -> 调用此工具，code="print(2**10)"
        - "写个排序算法测试一下" -> 调用此工具
        - "这段代码为什么报错？" -> 调用此工具，根据报错自我修正
    """
    return await _run_code(code, timeout)


async def _run_code(code: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """执行Python代码"""

    # 参数校验
    if not code or not code.strip():
        return "代码内容不能为空"

    code = code.strip()

    # 限制超时时间
    if timeout <= 0:
        timeout = DEFAULT_TIMEOUT
    elif timeout > 120:
        timeout = 120
        logger.warning(f"timeout超过最大值120秒，已自动调整")

    # 安全检查：检测危险导入
    warning = _check_dangerous_imports(code)
    if warning:
        return warning

    try:
        result = await _execute_in_subprocess(code, timeout)
        return result
    except Exception as e:
        logger.error(f"代码执行器错误: {e}")
        return f"代码执行失败: {str(e)}"


async def _execute_in_subprocess(code: str, timeout: int) -> str:
    """在子进程中执行代码"""

    # 构建安全包装代码：捕获stdout和stderr
    wrapped_code = _wrap_code(code)

    # 创建临时文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(wrapped_code)
        tmp_path = tmp.name

    try:
        start_time = time.time()

        # 在子进程中执行，限制资源
        process = await _async_subprocess_run(
            [sys.executable, tmp_path],
            timeout=timeout
        )

        elapsed = round(time.time() - start_time, 2)

        # 构建结果
        return _format_result(process, elapsed, timeout)

    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def _async_subprocess_run(cmd: list, timeout: int) -> dict:
    """异步运行子进程"""
    import asyncio

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            # 限制子进程环境
            env=_get_safe_env(),
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )

        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "returncode": proc.returncode,
            "timed_out": False,
        }

    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return {
            "stdout": "",
            "stderr": f"执行超时（{timeout}秒），进程已终止",
            "returncode": -1,
            "timed_out": True,
        }


def _get_safe_env() -> dict:
    """获取安全的环境变量（仅保留必要路径）"""
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "PYTHONIOENCODING": "utf-8",
        "LANG": "en_US.UTF-8",
    }
    return safe_env


def _wrap_code(code: str) -> str:
    """包装用户代码，添加输出捕获和异常处理"""
    template = '''# -*- coding: utf-8 -*-
import sys
import io

# 重定向stdout/stderr以捕获输出
_old_stdout = sys.stdout
_old_stderr = sys.stderr
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()

try:
    # 用户代码
{indented_code}
except SystemExit:
    pass
except Exception as e:
    # 将异常信息输出到stderr
    import traceback
    sys.stderr.write(traceback.format_exc())
finally:
    # 获取捕获的输出
    _stdout = sys.stdout.getvalue()
    _stderr = sys.stderr.getvalue()
    sys.stdout = _old_stdout
    sys.stderr = _old_stderr

    # 输出结果（JSON格式，方便解析）
    import json
    result = {{"stdout": _stdout, "stderr": _stderr}}
    print(json.dumps(result, ensure_ascii=False))
'''
    return template.format(indented_code=_indent_code(code))


def _indent_code(code: str) -> str:
    """将代码缩进4个空格（用于嵌套在try块中）"""
    lines = code.split("\n")
    return "\n".join("    " + line for line in lines)


def _format_result(process: dict, elapsed: float, timeout: int) -> str:
    """格式化执行结果"""
    stdout = process["stdout"]
    stderr = process["stderr"]
    returncode = process["returncode"]
    timed_out = process["timed_out"]

    # 尝试从stdout解析JSON结果
    actual_stdout = ""
    actual_stderr = ""
    try:
        result = json.loads(stdout)
        actual_stdout = result.get("stdout", "")
        actual_stderr = result.get("stderr", "")
    except (json.JSONDecodeError, IndexError):
        # 如果JSON解析失败，直接使用原始输出
        actual_stdout = stdout
        actual_stderr = stderr

    # 构建输出
    parts = []
    parts.append(f"⏱ 执行耗时: {elapsed}秒")

    if timed_out:
        parts.append(f"⚠️ 执行超时（限制{timeout}秒），请优化代码或增加超时时间")

    if returncode != 0:
        parts.append(f"❌ 退出码: {returncode}")

    # 标准输出
    if actual_stdout.strip():
        output = actual_stdout.strip()
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH]
            output += f"\n... (输出已截断，共 {len(actual_stdout.strip())} 字符)"
        parts.append(f"📤 输出:\n{output}")

    # 标准错误
    if actual_stderr.strip():
        error = actual_stderr.strip()
        if len(error) > MAX_OUTPUT_LENGTH:
            error = error[:MAX_OUTPUT_LENGTH]
            error += f"\n... (错误信息已截断)"
        parts.append(f"🔴 错误:\n{error}")

    # 无输出
    if not actual_stdout.strip() and not actual_stderr.strip() and returncode == 0:
        parts.append("📤 代码执行成功，无输出（如需查看结果，请使用 print() 输出）")

    return "\n\n".join(parts)


def _check_dangerous_imports(code: str) -> str:
    """检查代码中的危险导入"""
    import re

    # 匹配 import xxx / from xxx import
    import_pattern = r'^\s*(?:import|from)\s+(\w+)'
    matches = re.findall(import_pattern, code, re.MULTILINE)

    found_blocked = []
    for module_name in matches:
        if module_name in BLOCKED_MODULES:
            found_blocked.append(module_name)

    if found_blocked:
        blocked_str = "、".join(found_blocked)
        return (
            f"⚠️ 安全限制：代码中包含不允许的模块导入: {blocked_str}\n\n"
            f"被禁止的模块: {', '.join(sorted(BLOCKED_MODULES))}\n\n"
            f"沙箱环境仅允许使用安全的Python标准库和已安装的第三方库进行计算和数据处理。"
        )

    return ""
