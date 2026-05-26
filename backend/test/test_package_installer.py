"""package_installer 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.tools.package_installer.action import (
    pip_install, npm_install, pip_check, npm_check,
    pip_list, npm_list,
    _check_pkg_allowed, _find_npm,
)


# ─── 辅助函数测试 ───

def test_check_pkg_allowed():
    """测试包名检查 - 正常包名"""
    with patch("app.tools.package_installer.action.settings") as mock_settings:
        mock_settings.pkg_deny_set = {"crypto", "malware"}
        mock_settings.pkg_allow_set = set()
        # 不在禁止列表中，不在允许列表中（允许列表为空=不限制），应通过
        _check_pkg_allowed("requests")
    print("✅ _check_pkg_allowed 正常包名 测试通过")


def test_check_pkg_deny():
    """测试包名检查 - 禁止的包"""
    with patch("app.tools.package_installer.action.settings") as mock_settings:
        mock_settings.pkg_deny_set = {"crypto", "malware"}
        mock_settings.pkg_allow_set = set()
        try:
            _check_pkg_allowed("crypto")
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "禁止" in str(e)
    print("✅ _check_pkg_allowed 禁止包名 测试通过")


def test_check_pkg_allow_list():
    """测试包名检查 - 允许列表模式"""
    with patch("app.tools.package_installer.action.settings") as mock_settings:
        mock_settings.pkg_deny_set = set()
        mock_settings.pkg_allow_set = {"requests", "numpy"}
        try:
            _check_pkg_allowed("pandas")
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "不在允许" in str(e)
    print("✅ _check_pkg_allowed 允许列表模式 测试通过")


def test_find_npm():
    """测试 npm 查找"""
    # 无论系统有没有 npm，函数不应抛异常
    result = _find_npm()
    assert result is None or isinstance(result, str)
    print("✅ _find_npm 测试通过")


# ─── pip 工具测试 ───

async def test_pip_install_disabled():
    """测试 pip 安装被禁用"""
    with patch("app.tools.package_installer.action.settings") as mock_settings:
        mock_settings.PKG_ALLOW_PIP = False
        result = await pip_install.ainvoke({"packages": "requests"})
        assert "禁用" in result
    print("✅ pip安装被禁用 测试通过")


async def test_pip_install_deny_pkg():
    """测试 pip 安装禁止的包"""
    with patch("app.tools.package_installer.action.settings") as mock_settings:
        mock_settings.PKG_ALLOW_PIP = True
        mock_settings.pkg_deny_set = {"crypto"}
        mock_settings.pkg_allow_set = set()
        result = await pip_install.ainvoke({"packages": "crypto"})
        assert "❌" in result
        assert "禁止" in result
    print("✅ pip安装禁止包 测试通过")


async def test_pip_check_installed():
    """测试 pip 检查已安装的包"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Name: pip\nVersion: 24.0"

    with patch("app.tools.package_installer.action.asyncio.to_thread", return_value=mock_result):
        result = await pip_check.ainvoke({"package": "pip"})
        assert "已安装" in result
    print("✅ pip检查已安装包 测试通过")


async def test_pip_check_not_installed():
    """测试 pip 检查未安装的包"""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("app.tools.package_installer.action.asyncio.to_thread", return_value=mock_result):
        result = await pip_check.ainvoke({"package": "nonexistent_pkg_xyz"})
        assert "未安装" in result
    print("✅ pip检查未安装包 测试通过")


async def test_pip_list():
    """测试 pip 列表"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Package          Version\n---------------- -------\npip              24.0\nrequests         2.31.0"

    with patch("app.tools.package_installer.action.asyncio.to_thread", return_value=mock_result):
        result = await pip_list.ainvoke({"keyword": "pip"})
        assert "pip" in result
    print("✅ pip列表 测试通过")


# ─── npm 工具测试 ───

async def test_npm_install_disabled():
    """测试 npm 安装被禁用"""
    with patch("app.tools.package_installer.action.settings") as mock_settings:
        mock_settings.PKG_ALLOW_NPM = False
        result = await npm_install.ainvoke({"packages": "express"})
        assert "禁用" in result
    print("✅ npm安装被禁用 测试通过")


async def test_npm_install_no_npm():
    """测试 npm 不存在"""
    with patch("app.tools.package_installer.action.settings") as mock_settings,          patch("app.tools.package_installer.action._find_npm", return_value=None):
        mock_settings.PKG_ALLOW_NPM = True
        result = await npm_install.ainvoke({"packages": "express"})
        assert "未找到 npm" in result
    print("✅ npm不存在 测试通过")


async def test_npm_check_no_npm():
    """测试 npm_check 无 npm"""
    with patch("app.tools.package_installer.action._find_npm", return_value=None):
        result = await npm_check.ainvoke({"package": "express"})
        assert "未找到 npm" in result
    print("✅ npm_check无npm 测试通过")


async def test_npm_list_no_npm():
    """测试 npm_list 无 npm"""
    with patch("app.tools.package_installer.action._find_npm", return_value=None):
        result = await npm_list.ainvoke({})
        assert "未找到 npm" in result
    print("✅ npm_list无npm 测试通过")


# ─── 工具接口测试 ───

def test_tool_interfaces():
    """测试所有工具接口"""
    tools = [pip_install, npm_install, pip_check, npm_check, pip_list, npm_list]
    names = ["pip_install", "npm_install", "pip_check", "npm_check", "pip_list", "npm_list"]
    for tool_fn, name in zip(tools, names):
        assert tool_fn.name == name, f"工具名应为 {name}，实际为 {tool_fn.name}"
    print("✅ 所有工具接口 测试通过")


async def main():
    test_check_pkg_allowed()
    test_check_pkg_deny()
    test_check_pkg_allow_list()
    test_find_npm()
    await test_pip_install_disabled()
    await test_pip_install_deny_pkg()
    await test_pip_check_installed()
    await test_pip_check_not_installed()
    await test_pip_list()
    await test_npm_install_disabled()
    await test_npm_install_no_npm()
    await test_npm_check_no_npm()
    await test_npm_list_no_npm()
    test_tool_interfaces()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
