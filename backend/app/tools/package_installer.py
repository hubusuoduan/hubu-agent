"""包安装工具"""
import os
import shutil
import subprocess
import asyncio

from langchain_core.tools import tool
from loguru import logger

from app.config import settings


def _check_allowed(pkg_name: str):
    """检查包是否在允许/禁止列表中"""
    name = pkg_name.lower()
    allow = settings.pkg_allow_set
    deny = settings.pkg_deny_set
    if allow and name not in allow:
        raise ValueError(f"包 {pkg_name} 不在允许列表中")
    if name in deny:
        raise ValueError(f"包 {pkg_name} 在禁止列表中")


@tool(parse_docstring=True)
async def pip_install(packages: str) -> str:
    """使用 poetry add 安装 Python 包。

    Args:
        packages: 要安装的包名，多个包用空格分隔

    Returns:
        str: 安装结果
    """
    if not settings.PKG_ALLOW_PIP:
        return "❌ pip install 已被管理员禁用"

    try:
        pkg_tokens = packages.split()
        if not pkg_tokens:
            return "❌ 未指定要安装的包名"

        for pkg in pkg_tokens:
            _check_allowed(pkg.split("@")[0].split("==")[0].split(">=")[0].split("<=")[0].split("[")[0])

        backend_dir = str(settings.file_workspace_path().parent)
        cmd = ["poetry", "add"] + pkg_tokens

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True,
            timeout=settings.PKG_PIP_TIMEOUT, cwd=backend_dir, env=env,
        )

        if result.returncode == 0:
            output = result.stdout.strip() or result.stderr.strip()
            lines = [l for l in output.split("\n") if l.strip()]
            summary = "\n".join(lines[-5:]) if len(lines) > 5 else output
            return f"✅ pip 安装成功\n{summary}"
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return f"❌ pip 安装失败:\n{error}"

    except ValueError as e:
        return f"❌ {e}"
    except subprocess.TimeoutExpired:
        return f"❌ pip 安装超时（{settings.PKG_PIP_TIMEOUT}秒）"
    except Exception as e:
        logger.error(f"pip_install 错误: {e}")
        return f"❌ pip 安装异常: {e}"


@tool(parse_docstring=True)
async def npm_install(packages: str) -> str:
    """使用 npm 全局安装 Node.js 包。安装后 exec_js 可直接 require() 引用。

    Args:
        packages: 要安装的包名，多个包用空格分隔

    Returns:
        str: 安装结果
    """
    if not settings.PKG_ALLOW_NPM:
        return "❌ npm install 已被管理员禁用"

    try:
        npm_path = shutil.which("npm")
        if not npm_path:
            return "❌ 系统中未找到 npm，请先安装 Node.js"

        # 过滤 npm 标志参数，只保留包名
        NPM_FLAGS = {"-g", "--global", "-S", "--save", "-D", "--save-dev", "-O", "--save-optional", "-E", "--save-exact"}
        pkg_tokens = [t for t in packages.split() if t not in NPM_FLAGS]

        if not pkg_tokens:
            return "❌ 未指定要安装的包名"

        for pkg in pkg_tokens:
            _check_allowed(pkg.split("@")[0])

        cmd = [npm_path, "install", "-g", "--no-fund", "--no-audit", "--loglevel=error"] + pkg_tokens

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["NO_COLOR"] = "1"
        env["NPM_CONFIG_PROGRESS"] = "false"

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True,
            timeout=settings.PKG_NPM_TIMEOUT, env=env,
            encoding="utf-8", errors="replace",
        )

        if result.returncode == 0:
            output = result.stdout.strip() or result.stderr.strip()
            lines = [l for l in output.split("\n") if l.strip()]
            summary = "\n".join(lines[-5:]) if len(lines) > 5 else output
            return f"✅ npm 全局安装成功\n{summary}"
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return f"❌ npm 安装失败:\n{error}"

    except ValueError as e:
        return f"❌ {e}"
    except subprocess.TimeoutExpired:
        return f"❌ npm 安装超时（{settings.PKG_NPM_TIMEOUT}秒）"
    except Exception as e:
        logger.error(f"npm_install 错误: {e}")
        return f"❌ npm 安装异常: {e}"


@tool(parse_docstring=True)
async def pip_check(package: str) -> str:
    """检查 Python 包是否已安装及版本信息。

    Args:
        package: 包名

    Returns:
        str: 安装状态和版本
    """
    try:
        backend_dir = str(settings.file_workspace_path().parent)
        cmd = ["poetry", "show", package]

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True,
            timeout=30, cwd=backend_dir, env=env,
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            lines = [l for l in output.split("\n") if l.strip()][:3]
            return f"✅ {package} 已安装:\n" + "\n".join(lines)
        else:
            return f"❌ 未安装: {package}"

    except Exception as e:
        return f"❌ 检查失败: {e}"


@tool(parse_docstring=True)
async def npm_check(package: str) -> str:
    """检查 npm 全局包是否已安装及版本信息。

    Args:
        package: 包名

    Returns:
        str: 安装状态和版本
    """
    try:
        npm_path = shutil.which("npm")
        if not npm_path:
            return "❌ 系统中未找到 npm"

        cmd = [npm_path, "list", "-g", package, "--depth=0"]

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["NO_COLOR"] = "1"
        env["NPM_CONFIG_PROGRESS"] = "false"

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=30, env=env,
            encoding="utf-8", errors="replace",
        )

        stdout = result.stdout.strip()
        if result.returncode == 0 and stdout:
            return f"✅ {package} 已安装:\n{stdout}"
        else:
            return f"❌ 未安装: {package}"

    except Exception as e:
        return f"❌ 检查失败: {e}"


@tool(parse_docstring=True)
async def pip_list(keyword: str = "") -> str:
    """列出已安装的 Python 包。可按关键字过滤。

    Args:
        keyword: 过滤关键字，留空列出全部

    Returns:
        str: 已安装包的列表
    """
    try:
        backend_dir = str(settings.file_workspace_path().parent)
        cmd = ["poetry", "show"]

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True,
            timeout=30, cwd=backend_dir, env=env,
        )

        if result.returncode != 0:
            return f"❌ 获取列表失败: {result.stderr.strip()}"

        lines = result.stdout.strip().split("\n")
        if keyword:
            lines = [l for l in lines if keyword.lower() in l.lower()]

        if not lines or (len(lines) == 1 and not lines[0].strip()):
            return "📭 暂无已安装的 Python 包"

        output = "\n".join(lines)
        return f"📦 已安装的 Python 包（共 {len(lines)} 个）:\n{output}"

    except Exception as e:
        return f"❌ 获取列表失败: {e}"


@tool(parse_docstring=True)
async def npm_list() -> str:
    """列出已全局安装的 npm 包。

    Returns:
        str: 已安装包的列表
    """
    try:
        npm_path = shutil.which("npm")
        if not npm_path:
            return "❌ 系统中未找到 npm"

        cmd = [npm_path, "list", "-g", "--depth=0"]

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["NO_COLOR"] = "1"
        env["NPM_CONFIG_PROGRESS"] = "false"

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=30, env=env,
            encoding="utf-8", errors="replace",
        )

        if result.returncode != 0 and not result.stdout.strip():
            return "📭 暂无已全局安装的 npm 包"

        return f"📦 已全局安装的 npm包:\n{result.stdout.strip()}"

    except Exception as e:
        return f"❌ 获取列表失败: {e}"
