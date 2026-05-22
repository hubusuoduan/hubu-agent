"""knowledge_list 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
from app.tools.knowledge_list.action import knowledge_list, _list_knowledge


def test_tool_interface():
    """测试工具接口"""
    assert knowledge_list.name == "knowledge_list"
    desc = knowledge_list.description
    assert "知识库" in desc or "列表" in desc
    print("✅ 工具接口 测试通过")


async def test_tool_invoke_no_keyword():
    """测试工具调用 - 无关键词"""
    result = await knowledge_list.ainvoke({"keyword": ""})
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"✅ 工具调用(无关键词) 测试通过 - 返回: {result[:50]}...")


async def test_tool_invoke_with_keyword():
    """测试工具调用 - 带关键词"""
    result = await knowledge_list.ainvoke({"keyword": "测试"})
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"✅ 工具调用(带关键词) 测试通过 - 返回: {result[:50]}...")


async def test_list_knowledge_function():
    """测试底层函数"""
    result = await _list_knowledge("不存在的关键词xyz")
    assert isinstance(result, str)
    assert "未找到" in result or "没有任何" in result or "数据库" in result
    print("✅ 底层函数 测试通过")


async def main():
    test_tool_interface()
    await test_tool_invoke_no_keyword()
    await test_tool_invoke_with_keyword()
    await test_list_knowledge_function()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
