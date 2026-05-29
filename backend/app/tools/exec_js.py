"""JavaScript 代码执行工具"""
import os
import shutil
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


def _get_npm_global_modules() -> str:
    """获取 npm 全局 node_modules 路径"""
    try:
        npm = shutil.which("npm")
        if not npm:
            return ""
        r = subprocess.run([npm, "root", "-g"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        if r.returncode == 0:
            path = r.stdout.strip()
            if os.path.isdir(path):
                return path
    except Exception:
        pass
    return ""


@tool(parse_docstring=True)
async def exec_js(code: str, timeout: int = 0) -> str:
    """执行 JavaScript 代码并返回输出结果。需要 npm 包时先用 npm_install 全局安装。

    Args:
        code: 要执行的 JavaScript 代码
        timeout: 超时秒数，0 表示使用默认值

    Returns:
        str: 代码执行结果
    """
    node_path = shutil.which("node")
    if not node_path:
        return "❌ 系统中未找到 node，请先安装 Node.js"

    from app.services.settings_service import SettingsFactory
    default_timeout = SettingsFactory.get(key="CODE_EXEC_TIMEOUT")
    max_timeout = SettingsFactory.get(key="CODE_EXEC_MAX_TIMEOUT")
    actual_timeout = timeout if timeout > 0 else default_timeout
    actual_timeout = min(actual_timeout, max_timeout)
    max_output = settings.CODE_EXEC_MAX_OUTPUT

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name

    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        # 设置 NODE_PATH 指向全局 node_modules，使 require() 能找到全局安装的包
        global_modules = _get_npm_global_modules()
        if global_modules:
            existing = env.get("NODE_PATH", "")
            env["NODE_PATH"] = f"{global_modules}{os.pathsep}{existing}" if existing else global_modules

        start = time.time()
        proc = await asyncio.to_thread(
            subprocess.run,
            [node_path, tmp_path],
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
        logger.error(f"exec_js 错误: {e}")
        return f"❌ 执行异常: {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
