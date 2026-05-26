"""file_manager 工具简单测试 - 用 __main__ 直接运行"""
import os
import shutil
import base64
import tempfile
from pathlib import Path
from unittest.mock import patch, PropertyMock

from app.tools.file_manager.action import (
    file_write, file_read, file_read_bytes, file_write_bytes,
    file_list, file_delete, file_move, file_mkdir,
    file_exists, file_info,
    _resolve_path, _check_extension, _fmt_size,
)


# ─── 辅助函数测试 ───

def test_fmt_size():
    """测试文件大小格式化"""
    assert _fmt_size(0) == "0B"
    assert _fmt_size(512) == "512B"
    assert _fmt_size(1024) == "1.0KB"
    assert _fmt_size(1048576) == "1.0MB"
    assert _fmt_size(1073741824) == "1.0GB"
    print("✅ _fmt_size 测试通过")


def test_resolve_path():
    """测试路径解析 - 正常路径"""
    from app.config import settings
    workspace = settings.file_workspace_path
    resolved = _resolve_path("test/hello.txt")
    assert str(resolved).startswith(str(workspace))
    print("✅ _resolve_path 正常路径 测试通过")


def test_resolve_path_traversal():
    """测试路径解析 - 防止路径穿越"""
    try:
        _resolve_path("../../etc/passwd")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "越权" in str(e)
    print("✅ _resolve_path 防路径穿越 测试通过")


def test_check_extension_deny():
    """测试扩展名检查 - 禁止的扩展名"""
    try:
        _check_extension("evil.exe")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "禁止" in str(e)
    print("✅ _check_extension 禁止扩展名 测试通过")


# ─── 工具函数测试（使用临时目录模拟工作区）───

def _setup_workspace():
    """创建临时工作区"""
    tmp = tempfile.mkdtemp(prefix="hubu_test_")
    return Path(tmp)


def _cleanup_workspace(path: Path):
    """清理临时工作区"""
    if path.exists():
        shutil.rmtree(path)


def test_file_write_and_read():
    """测试文件写入和读取"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe", ".bat", ".sh"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            # 写入
            result = file_write("test/hello.txt", "Hello, Hubu!")
            assert "✅" in result
            assert "hello.txt" in result

            # 读取
            result = file_read("test/hello.txt")
            assert "Hello, Hubu!" in result
    finally:
        _cleanup_workspace(workspace)
    print("✅ 文件写入和读取 测试通过")


def test_file_write_append():
    """测试追加写入"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe", ".bat", ".sh"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            file_write("append.txt", "第一行")
            result = file_write("append.txt", "\n第二行", mode="append")
            assert "✅" in result

            content = file_read("append.txt")
            assert "第一行" in content
            assert "第二行" in content
    finally:
        _cleanup_workspace(workspace)
    print("✅ 追加写入 测试通过")


def test_file_read_not_exist():
    """测试读取不存在的文件"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()

            result = file_read("nonexistent.txt")
            assert "❌" in result
            assert "不存在" in result
    finally:
        _cleanup_workspace(workspace)
    print("✅ 读取不存在文件 测试通过")


def test_file_write_bytes_and_read_bytes():
    """测试二进制文件写入和读取"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            # 写入二进制
            raw_data = b"Binary content here"
            b64 = base64.b64encode(raw_data).decode("ascii")
            result = file_write_bytes("data.bin", b64)
            assert "✅" in result

            # 读取二进制
            result = file_read_bytes("data.bin")
            decoded = base64.b64decode(result)
            assert decoded == raw_data
    finally:
        _cleanup_workspace(workspace)
    print("✅ 二进制文件写入和读取 测试通过")


def test_file_list():
    """测试目录列表"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            file_write("a.txt", "aaa")
            file_write("b.txt", "bbb")
            file_mkdir("subdir")

            result = file_list(".")
            assert "a.txt" in result
            assert "b.txt" in result
            assert "subdir" in result
    finally:
        _cleanup_workspace(workspace)
    print("✅ 目录列表 测试通过")


def test_file_delete():
    """测试文件删除"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            file_write("del_me.txt", "bye")
            result = file_delete("del_me.txt")
            assert "✅" in result

            # 确认已删除
            result = file_exists("del_me.txt")
            assert "不存在" in result
    finally:
        _cleanup_workspace(workspace)
    print("✅ 文件删除 测试通过")


def test_file_move():
    """测试文件移动/重命名"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            file_write("old.txt", "content")
            result = file_move("old.txt", "new.txt")
            assert "✅" in result

            # 旧文件不存在，新文件存在
            assert "不存在" in file_exists("old.txt")
            assert "存在" in file_exists("new.txt")
    finally:
        _cleanup_workspace(workspace)
    print("✅ 文件移动 测试通过")


def test_file_mkdir():
    """测试创建目录"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()

            result = file_mkdir("deep/nested/dir")
            assert "✅" in result
            assert (workspace / "deep" / "nested" / "dir").is_dir()
    finally:
        _cleanup_workspace(workspace)
    print("✅ 创建目录 测试通过")


def test_file_exists():
    """测试文件存在检查"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            result = file_exists("no_such_file.txt")
            assert "不存在" in result

            file_write("exists.txt", "hi")
            result = file_exists("exists.txt")
            assert "存在" in result
    finally:
        _cleanup_workspace(workspace)
    print("✅ 文件存在检查 测试通过")


def test_file_info():
    """测试文件详细信息"""
    workspace = _setup_workspace()
    try:
        with patch("app.tools.file_manager.action.settings") as mock_settings:
            mock_settings.file_workspace_path = workspace
            mock_settings.file_deny_ext_set = {".exe"}
            mock_settings.file_allow_ext_set = set()
            mock_settings.FILE_MAX_SIZE = 52428800

            file_write("info.txt", "some content here")
            result = file_info("info.txt")
            assert "文件" in result
            assert ".txt" in result
            assert "修改时间" in result
    finally:
        _cleanup_workspace(workspace)
    print("✅ 文件详细信息 测试通过")


def test_tool_interfaces():
    """测试所有工具接口"""
    tools = [file_write, file_read, file_write_bytes, file_read_bytes,
             file_list, file_delete, file_move, file_mkdir, file_exists, file_info]
    names = ["file_write", "file_read", "file_write_bytes", "file_read_bytes",
             "file_list", "file_delete", "file_move", "file_mkdir", "file_exists", "file_info"]
    for tool_fn, name in zip(tools, names):
        assert tool_fn.name == name, f"工具名应为 {name}，实际为 {tool_fn.name}"
    print("✅ 所有工具接口 测试通过")


if __name__ == "__main__":
    test_fmt_size()
    test_resolve_path()
    test_resolve_path_traversal()
    test_check_extension_deny()
    test_file_write_and_read()
    test_file_write_append()
    test_file_read_not_exist()
    test_file_write_bytes_and_read_bytes()
    test_file_list()
    test_file_delete()
    test_file_move()
    test_file_mkdir()
    test_file_exists()
    test_file_info()
    test_tool_interfaces()
    print("\n🎉 所有测试通过！")
