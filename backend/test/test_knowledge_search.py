"""knowledge_search 工具简单测试 - 用 __main__ 直接运行"""
import asyncio
from app.tools.knowledge_search.action import knowledge_search, _search_knowledge


async def test_empty_query():
    """测试空查询"""
    result = await _search_knowledge("", "kb_001")
    assert "查询内容不能为空" in result
    print("✅ 空查询校验 测试通过")


async def test_whitespace_query():
    """测试纯空白查询"""
    result = await _search_knowledge("   ", "kb_001")
    assert "查询内容不能为空" in result
    print("✅ 空白查询校验 测试通过")


async def test_empty_knowledge_ids():
    """测试空知识库ID"""
    result = await _search_knowledge("年假制度", "")
    assert "知识库ID不能为空" in result
    print("✅ 空知识库ID校验 测试通过")


async def test_invalid_knowledge_ids():
    """测试无效知识库ID格式"""
    result = await _search_knowledge("年假制度", ",,,")
    assert "知识库ID格式无效" in result
    print("✅ 无效知识库ID格式 测试通过")


def test_tool_interface():
    """测试工具接口"""
    assert knowledge_search.name == "knowledge_search"
    desc = knowledge_search.description
    assert "知识库" in desc or "检索" in desc
    print("✅ 工具接口 测试通过")


async def test_tool_invoke_with_invalid_params():
    """测试工具调用 - 无效参数应返回错误提示"""
    result = await knowledge_search.ainvoke({"query": "", "knowledge_ids": "kb_001"})
    assert "查询内容不能为空" in result
    print("✅ 工具调用(无效参数) 测试通过")


async def main():
    await test_empty_query()
    await test_whitespace_query()
    await test_empty_knowledge_ids()
    await test_invalid_knowledge_ids()
    test_tool_interface()
    await test_tool_invoke_with_invalid_params()
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
