"""report_generator 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
import os
from app.tools.report_generator.action import report_generator, _generate_report, _build_file_path, _format_content


async def test_empty_title():
    """测试空标题"""
    result = await _generate_report("", "内容")
    assert "标题不能为空" in result
    print("✅ 空标题校验 测试通过")


async def test_empty_content():
    """测试空内容"""
    result = await _generate_report("报告", "")
    assert "内容不能为空" in result
    print("✅ 空内容校验 测试通过")


async def test_invalid_format():
    """测试无效格式"""
    result = await _generate_report("报告", "内容", "pdf")
    assert "不支持" in result
    print("✅ 无效格式校验 测试通过")


async def test_build_file_path():
    """测试文件路径构建"""
    file_name, file_path = _build_file_path("测试报告", "markdown")
    assert file_name.endswith(".md")
    assert "测试报告" in file_name
    print(f"✅ 文件路径构建 测试通过 - {file_name}")


async def test_build_file_path_special_chars():
    """测试特殊字符标题"""
    file_name, file_path = _build_file_path("报告:测试/特殊*字符", "txt")
    assert ":" not in file_name
    assert "/" not in file_name
    assert "*" not in file_name
    assert file_name.endswith(".txt")
    print("✅ 特殊字符标题 测试通过")


async def test_format_markdown():
    """测试 Markdown 格式化"""
    result = _format_content("测试", "# 标题\n内容", "markdown")
    assert "# 测试" in result
    assert "生成时间" in result
    print("✅ Markdown格式化 测试通过")


async def test_format_txt():
    """测试纯文本格式化"""
    result = _format_content("测试", "# 标题\n**加粗**", "txt")
    assert "测试" in result
    assert "#" not in result  # Markdown 标记应被去除
    assert "加粗" in result
    print("✅ 纯文本格式化 测试通过")


async def test_format_html():
    """测试 HTML 格式化"""
    result = _format_content("测试", "# 标题\n内容", "html")
    assert "<html" in result
    assert "<h" in result
    assert "生成时间" in result
    print("✅ HTML格式化 测试通过")


async def test_tool_interface():
    """测试工具接口"""
    assert report_generator.name == "report_generator"
    desc = report_generator.description
    assert "报告" in desc or "文件" in desc
    print("✅ 工具接口 测试通过")


async def test_generate_markdown_report():
    """测试生成 Markdown 报告"""
    result = await _generate_report(
        "测试报告",
        "# 概述\n\n这是一份测试报告。\n\n## 详情\n\n- 项目1\n- 项目2",
        "markdown"
    )
    assert "报告生成成功" in result
    assert "下载链接" in result
    print(f"✅ 生成Markdown报告 测试通过")


async def test_generate_html_report():
    """测试生成 HTML 报告"""
    result = await _generate_report(
        "HTML测试报告",
        "这是一份HTML格式的报告。",
        "html"
    )
    assert "报告生成成功" in result
    assert ".html" in result
    print("✅ 生成HTML报告 测试通过")


async def main():
    await test_empty_title()
    await test_empty_content()
    await test_invalid_format()
    await test_build_file_path()
    await test_build_file_path_special_chars()
    await test_format_markdown()
    await test_format_txt()
    await test_format_html()
    await test_tool_interface()
    await test_generate_markdown_report()
    await test_generate_html_report()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
