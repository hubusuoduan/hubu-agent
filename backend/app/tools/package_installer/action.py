"""包安装器 - 安装和检查 pip/npm 依赖包"""
import sys
import asyncio
import subprocess
import shutil
from pathlib import Path
from loguru import logger
from langchain.tools import tool

from app.config import settings


# ─── 安全校验 ───

def _check_pkg_allowed(name: str) -> None:
    """检查包名是否在允许/禁止列表中"""
    name_lower = name.strip().lower()
    deny_set = settings.pkg_deny_set
    allow_set = settings.pkg_allow_set

    if name_lower in deny_set:
        raise ValueError(f"包 '{name}' 在禁止安装列表中")
    if allow_set and name_lower not in allow_set:
        raise ValueError(f"包 '{name}' 不在允许安装列表中")


def _find_npm() -> str | None:
    """查找系统中的 npm 可执行文件"""
    return shutil.which("npm")


# ─── pip 工具 ───

@tool(parse_docstring=True)
async def pip_install(packages: str, upgrade: bool = False) -> str:
    """
    使用 poetry add 安装 Python 包，包会持久化到 pyproject.toml 和 poetry.lock 中。

    Args:
        packages (str): 要安装的包名，多个包用空格分隔，支持版本指定如 'requests>=2.28'
        upgrade (bool): 是否升级已安装的包，默认False

    Returns:
        str: 安装结果，包含成功/失败信息
    """
    if not settings.PKG_ALLOW_PIP:
        return "❌ pip install 已被管理员禁用"

    try:
        # 逐个检查包名（提取包名，去除版本号）
        for pkg in packages.split():
            pkg_name = pkg.split(">=")[0].split("<=")[0].split("==")[0].split(">")[0].split("<")[0].split("[")[0]
            _check_pkg_allowed(pkg_name)

        # 使用 poetry add 安装，包会写入 pyproject.toml 并更新 lock 文件
        cmd = ["poetry", "add"]
        cmd.extend(packages.split())

        # poetry 命令需要在 backend 目录（pyproject.toml 所在目录）下执行
        backend_dir = str(Path(__file__).resolve().parent.parent.parent.parent)

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True,
            timeout=settings.PKG_PIP_TIMEOUT,
            cwd=backend_dir,
        )

        if result.returncode == 0:
            output = result.stdout.strip() or result.stderr.strip()
            lines = [l for l in output.split("\n") if l.strip()]
            summary = "\n".join(lines[-5:]) if len(lines) > 5 else output
            return f"✅ poetry add 安装成功\n{summary}"
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return f"❌ poetry add 安装失败:\n{error}"

    except ValueError as e:
        return f"❌ {e}"
    except subprocess.TimeoutExpired:
        return f"❌ 安装超时（{settings.PKG_PIP_TIMEOUT}秒）"
    except Exception as e:
        logger.error(f"pip_install 错误: {e}")
        return f"❌ 安装异常: {e}"


@tool(parse_docstring=True)
async def npm_install(packages: str, global_install: bool = False) -> str:
    """
    使用 npm 安装 Node.js 包。部分 Skill（如 docx、pptx）需要 npm 全局安装工具。

    Args:
        packages (str): 要安装的包名，多个包用空格分隔
        global_install (bool): 是否全局安装（-g），默认False

    Returns:
        str: 安装结果
    """
    if not settings.PKG_ALLOW_NPM:
        return "❌ npm install 已被管理员禁用"

    try:
        npm_path = _find_npm()
        if not npm_path:
            return "❌ 系统中未找到 npm，请先安装 Node.js"

        for pkg in packages.split():
            pkg_name = pkg.split("@")[0]
            _check_pkg_allowed(pkg_name)

        cmd = [npm_path, "install", "--no-fund", "--no-audit", "--loglevel=error"]
        if global_install:
            cmd.append("-g")
        cmd.extend(packages.split())

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True,
            timeout=settings.PKG_NPM_TIMEOUT
        )

        if result.returncode == 0:
            output = result.stdout.strip() or result.stderr.strip()
            lines = [l for l in output.split("\n") if l.strip()]
            summary = "\n".join(lines[-5:]) if len(lines) > 5 else output
            return f"✅ npm 安装成功\n{summary}"
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
    """
    检查 Python 包是否已安装及其版本信息。

    Args:
        package (str): 要检查的包名

    Returns:
        str: 包的安装状态和版本
    """
    try:
        cmd = [sys.executable, "-m", "pip", "show", package]
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            return f"✅ 已安装:\n{result.stdout.strip()}"
        else:
            return f"❌ 未安装: {package}"

    except Exception as e:
        logger.error(f"pip_check 错误: {e}")
        return f"❌ 检查失败: {e}"


@tool(parse_docstring=True)
async def npm_check(package: str) -> str:
    """
    检查 npm 包是否已安装及其版本信息。

    Args:
        package (str): 要检查的包名

    Returns:
        str: 包的安装状态和版本
    """
    try:
        npm_path = _find_npm()
        if not npm_path:
            return "❌ 系统中未找到 npm"

        # 先检查全局
        cmd_global = [npm_path, "list", "-g", package, "--depth=0"]
        result_global = await asyncio.to_thread(
            subprocess.run, cmd_global, capture_output=True, text=True, timeout=30
        )

        # 再检查本地
        cmd_local = [npm_path, "list", package, "--depth=0"]
        result_local = await asyncio.to_thread(
            subprocess.run, cmd_local, capture_output=True, text=True, timeout=30
        )

        parts = []
        if result_global.returncode == 0:
            parts.append(f"🌐 全局安装:\n{result_global.stdout.strip()}")
        if result_local.returncode == 0:
            parts.append(f"📁 本地安装:\n{result_local.stdout.strip()}")

        if parts:
            return f"✅ {package} 已安装:\n" + "\n".join(parts)
        else:
            return f"❌ 未安装: {package}"

    except Exception as e:
        logger.error(f"npm_check 错误: {e}")
        return f"❌ 检查失败: {e}"


@tool(parse_docstring=True)
async def pip_list(keyword: str = "") -> str:
    """
    列出已安装的 Python 包。可按关键字过滤。

    Args:
        keyword (str): 过滤关键字，留空列出全部

    Returns:
        str: 已安装包的列表
    """
    try:
        cmd = [sys.executable, "-m", "pip", "list", "--format=columns"]
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            return f"❌ 获取包列表失败"

        lines = result.stdout.strip().split("\n")
        if keyword:
            keyword_lower = keyword.lower()
            lines = [l for l in lines if keyword_lower in l.lower()]

        if len(lines) <= 2:
            return f"📭 未找到匹配 '{keyword}' 的包"

        output = "\n".join(lines)
        count = len(lines) - 2  # 减去表头
        return f"📦 已安装的 Python 包（共 {count} 个）:\n{output}"

    except Exception as e:
        logger.error(f"pip_list 错误: {e}")
        return f"❌ 获取列表失败: {e}"


@tool(parse_docstring=True)
async def npm_list(global_only: bool = True) -> str:
    """
    列出已安装的 npm 包。

    Args:
        global_only (bool): 是否只列出全局安装的包，默认True

    Returns:
        str: 已安装包的列表
    """
    try:
        npm_path = _find_npm()
        if not npm_path:
            return "❌ 系统中未找到 npm"

        cmd = [npm_path, "list", "--depth=0"]
        if global_only:
            cmd.append("-g")

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0 and not result.stdout.strip():
            return "❌ 获取 npm 包列表失败"

        output = result.stdout.strip()
        scope = "全局" if global_only else "本地"
        return f"📦 已安装的 npm 包（{scope}）:\n{output}"

    except Exception as e:
        logger.error(f"npm_list 错误: {e}")
        return f"❌ 获取列表失败: {e}"
