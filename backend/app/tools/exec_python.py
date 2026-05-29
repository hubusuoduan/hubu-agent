"""Python 代码执行工具"""
import os
import sys
import subprocess
import tempfile
import time
import asyncio

from langchain_core.tools import tool
from loguru import logger

from app.config import settings


def _workspace() -> str:
    """获取当前工作区路径"""
    from app.callbacks import current_workspace_dir
    ws = current_workspace_dir.get("")
    return ws if ws else str(settings.file_workspace_path())


@tool(parse_docstring=True)
async def exec_python(code: str, timeout: int = 0) -> str:
    """执行 Python 代码并返回输出结果。

    Args:
        code: 要执行的 Python 代码
        timeout: 超时秒数，0 表示使用默认值

    Returns:
        str: 代码执行结果
    """
    from app.services.settings_service import SettingsFactory
    default_timeout = SettingsFactory.get(key="CODE_EXEC_TIMEOUT")
    max_timeout = SettingsFactory.get(key="CODE_EXEC_MAX_TIMEOUT")
    actual_timeout = timeout if timeout > 0 else default_timeout
    actual_timeout = min(actual_timeout, max_timeout)
    max_output = settings.CODE_EXEC_MAX_OUTPUT

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name

    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        start = time.time()
        proc = await asyncio.to_thread(
            subprocess.run,
            [sys.executable, "-u", tmp_path],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=actual_timeout, env=env,
            cwd=_workspace(),
        )
        elapsed = time.time() - start

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        if len(stdout) > max_output:
            stdout = stdout[:max_output] + f"\n... (输出截断，共 {len(stdout)} 字符)"
        if len(stderr) > max_output:
            stderr = stderr[:max_output] + f"\n... (错误截断，共 {len(stderr)} 字符)"

        parts = []
        if stdout.strip():
            parts.append(stdout.strip())
        if stderr.strip():
            parts.append(f"[stderr]\n{stderr.strip()}")
        result = "\n".join(parts) if parts else "(无输出)"

        if proc.returncode != 0:
            result = f"❌ 执行失败 (exit code {proc.returncode})\n{result}"

        return result

    except subprocess.TimeoutExpired:
        return f"❌ 执行超时（{actual_timeout}秒）"
    except Exception as e:
        logger.error(f"exec_python 错误: {e}")
        return f"❌ 执行异常: {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
