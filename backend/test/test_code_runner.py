"""code_runner 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
from app.tools.code_runner.action import code_runner, _run_code, _check_dangerous_imports


async def test_empty_code():
    """测试空代码"""
    result = await _run_code("", 10)
    assert "代码内容不能为空" in result
    print("✅ 空代码校验 测试通过")


async def test_simple_calc():
    """测试简单计算"""
    result = await _run_code("print(2 ** 10)", 10)
    assert "1024" in result
    print("✅ 简单计算 测试通过")


async def test_multi_line():
    """测试多行代码"""
    code = """
nums = [3, 1, 4, 1, 5, 9]
nums.sort()
print(nums)
"""
    result = await _run_code(code, 10)
    assert "[1, 1, 3, 4, 5, 9]" in result
    print("✅ 多行代码 测试通过")


async def test_error_code():
    """测试错误代码 - 应返回报错信息"""
    result = await _run_code("x = 1 / 0", 10)
    assert "ZeroDivisionError" in result or "错误" in result
    print("✅ 错误代码 测试通过")


async def test_no_output():
    """测试无输出代码"""
    result = await _run_code("x = 42", 10)
    assert "无输出" in result or "执行成功" in result
    print("✅ 无输出代码 测试通过")


async def test_dangerous_import():
    """测试危险导入检测"""
    result = _check_dangerous_imports("import os\nprint('hello')")
    assert "安全限制" in result
    assert "os" in result
    print("✅ 危险导入检测 测试通过")


async def test_safe_code():
    """测试安全代码（无危险导入）"""
    result = _check_dangerous_imports("import math\nprint(math.pi)")
    assert result == ""
    print("✅ 安全代码检测 测试通过")


async def test_tool_interface():
    """测试工具接口"""
    assert code_runner.name == "code_runner"
    desc = code_runner.description
    assert "代码" in desc or "执行" in desc
    print("✅ 工具接口 测试通过")


async def test_tool_invoke():
    """测试工具调用"""
    result = await code_runner.ainvoke({"code": "print('Hello, Hubu Agent!')"})
    assert "Hello, Hubu Agent!" in result
    print("✅ 工具调用 测试通过")


async def main():
    await test_empty_code()
    await test_simple_calc()
    await test_multi_line()
    await test_error_code()
    await test_no_output()
    await test_dangerous_import()
    await test_safe_code()
    await test_tool_interface()
    await test_tool_invoke()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
