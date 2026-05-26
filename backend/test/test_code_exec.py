"""code_exec 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
from unittest.mock import patch, MagicMock
from app.tools.code_exec.action import code_exec, _run_code, _format_result


async def test_empty_code():
    """测试空代码"""
    result = await _run_code("", 10)
    assert "代码内容不能为空" in result
    print("✅ 空代码校验 测试通过")


async def test_simple_print():
    """测试简单打印"""
    result = await _run_code("print('Hello, World!')", 30)
    assert "Hello, World!" in result
    print("✅ 简单打印 测试通过")


async def test_calculation():
    """测试数学计算"""
    result = await _run_code("print(2 ** 20)", 30)
    assert "1048576" in result
    print("✅ 数学计算 测试通过")


async def test_error_code():
    """测试错误代码"""
    result = await _run_code("raise ValueError('test error')", 30)
    assert "ValueError" in result or "错误" in result
    print("✅ 错误代码 测试通过")


async def test_no_output():
    """测试无输出代码"""
    result = await _run_code("x = 42", 30)
    assert "无输出" in result or "执行成功" in result
    print("✅ 无输出代码 测试通过")


async def test_import_os():
    """测试可以导入 os（完整环境，不受沙箱限制）"""
    result = await _run_code("import os; print(os.name)", 30)
    # 在完整环境中，os 应该可以正常导入
    assert "错误" not in result or "nt" in result or "posix" in result
    print("✅ 完整环境导入os 测试通过")


def test_format_result():
    """测试结果格式化"""
    result = _format_result("hello", "", 0, 0.5, 30, False)
    assert "0.5秒" in result
    assert "hello" in result

    # 测试超时
    result = _format_result("", "timeout error", -1, 30.0, 30, True)
    assert "超时" in result

    # 测试无输出
    result = _format_result("", "", 0, 0.1, 30, False)
    assert "无输出" in result
    print("✅ 结果格式化 测试通过")


async def test_tool_interface():
    """测试工具接口"""
    assert code_exec.name == "code_exec"
    assert "执行" in code_exec.description or "代码" in code_exec.description
    print("✅ 工具接口 测试通过")


async def test_tool_invoke():
    """测试工具调用"""
    result = await code_exec.ainvoke({"code": "print('Hubu Agent!')"})
    assert "Hubu Agent!" in result
    print("✅ 工具调用 测试通过")


async def main():
    await test_empty_code()
    await test_simple_print()
    await test_calculation()
    await test_error_code()
    await test_no_output()
    await test_import_os()
    test_format_result()
    await test_tool_interface()
    await test_tool_invoke()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
