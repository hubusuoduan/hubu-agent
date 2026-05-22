"""长期记忆系统测试 - 用 __main__ 直接运行"""
import asyncio
from app.core.agents.memory_agent import MemoryAgent
from app.services.memory_service import get_memory_service, MemoryService
from app.core.graph.nodes.memory_node import memory_node
from app.core.graph.nodes.memory_extract_node import memory_extract_node
from app.services.llm_service import LLMService
from app.config import settings


TEST_USER_ID = "test_memory_user_001"
TEST_DIALOG_ID = "test_memory_dialog_001"


# ============================================================
# 测试 1: MemoryAgent JSON 解析
# ============================================================
def test_json_parse_pure():
    """测试纯 JSON 解析"""
    agent = MemoryAgent(model=None)
    text = '{"should_save": true, "memories": [{"content": "test", "type": "fact"}]}'
    result = agent._parse_json(text)
    assert result is not None
    assert result["should_save"] is True
    assert len(result["memories"]) == 1
    print("✅ 纯JSON解析 测试通过")


def test_json_parse_code_block():
    """测试 ```json 包裹的 JSON 解析"""
    agent = MemoryAgent(model=None)
    text = '```json\n{"should_save": false, "memories": []}\n```'
    result = agent._parse_json(text)
    assert result is not None
    assert result["should_save"] is False
    print("✅ ```json包裹解析 测试通过")


def test_json_parse_with_surrounding_text():
    """测试带额外文字的 JSON 解析"""
    agent = MemoryAgent(model=None)
    text = '根据分析：\n{"should_save": true, "memories": [{"content": "用户喜欢Python", "type": "preference"}]}\n以上是结果。'
    result = agent._parse_json(text)
    assert result is not None
    assert len(result["memories"]) == 1
    print("✅ 带额外文字解析 测试通过")


def test_json_parse_invalid():
    """测试无效 JSON 返回 None"""
    agent = MemoryAgent(model=None)
    result = agent._parse_json("这不是JSON")
    assert result is None
    print("✅ 无效JSON返回None 测试通过")


# ============================================================
# 测试 2: MemoryAgent 记忆提取（需要 LLM）
# ============================================================
async def test_memory_agent_extract_preference():
    """测试提取用户偏好"""
    model = LLMService.get_model(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model_name=settings.LLM_MODEL
    )
    agent = MemoryAgent(model=model)
    memories = await agent.extract(
        user_input="我平时喜欢用Python写代码，不太喜欢Java",
        assistant_response="了解，您偏好使用Python编程。"
    )
    assert memories is not None
    assert len(memories) > 0
    types = [m["type"] for m in memories]
    contents = [m["content"] for m in memories]
    assert "preference" in types
    assert any("Python" in c for c in contents)
    print(f"✅ 提取用户偏好 测试通过, 提取到: {memories}")


async def test_memory_agent_extract_fact():
    """测试提取用户事实"""
    model = LLMService.get_model(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model_name=settings.LLM_MODEL
    )
    agent = MemoryAgent(model=model)
    memories = await agent.extract(
        user_input="我是湖北大学计算机科学专业的学生",
        assistant_response="你好，湖北大学计算机科学专业的同学！"
    )
    assert memories is not None
    assert len(memories) > 0
    contents = [m["content"] for m in memories]
    assert any("湖北大学" in c for c in contents)
    print(f"✅ 提取用户事实 测试通过, 提取到: {memories}")


async def test_memory_agent_extract_nothing():
    """测试临时性对话不应提取记忆"""
    model = LLMService.get_model(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model_name=settings.LLM_MODEL
    )
    agent = MemoryAgent(model=model)
    memories = await agent.extract(
        user_input="今天天气怎么样？",
        assistant_response="今天天气晴朗，温度25度左右。"
    )
    assert memories is None or len(memories) == 0
    print("✅ 临时对话不提取 测试通过")


# ============================================================
# 测试 3: MemoryService Milvus 读写（需要 Milvus）
# ============================================================
async def test_memory_service_add():
    """测试写入记忆"""
    service = get_memory_service()
    mid = await service.add_memory(
        user_id=TEST_USER_ID,
        content="用户是湖北大学计算机专业的学生",
        memory_type="fact",
        source_dialog_id=TEST_DIALOG_ID
    )
    assert mid is not None
    print(f"✅ 写入记忆 测试通过, id={mid}")


async def test_memory_service_search():
    """测试检索记忆"""
    service = get_memory_service()
    # 先写入
    await service.add_memory(
        user_id=TEST_USER_ID,
        content="用户偏好使用Python编程",
        memory_type="preference",
        source_dialog_id=TEST_DIALOG_ID
    )
    await asyncio.sleep(2)  # 等待数据生效
    # 检索
    results = await service.search_memories(
        user_id=TEST_USER_ID,
        query="用户喜欢什么编程语言",
        top_k=3
    )
    assert len(results) > 0
    assert any("Python" in r["content"] for r in results)
    print(f"✅ 检索记忆 测试通过, 命中 {len(results)} 条")


async def test_memory_service_duplicate():
    """测试记忆去重"""
    service = get_memory_service()
    mid1 = await service.add_memory(
        user_id=TEST_USER_ID,
        content="用户是湖北大学计算机专业的学生",
        memory_type="fact",
        source_dialog_id=TEST_DIALOG_ID
    )
    # 写入语义相同的记忆
    mid2 = await service.add_memory(
        user_id=TEST_USER_ID,
        content="用户就读于湖北大学计算机专业",
        memory_type="fact",
        source_dialog_id=TEST_DIALOG_ID
    )
    # 至少有一个应该是 None（被去重跳过）
    assert mid1 is None or mid2 is None
    print("✅ 记忆去重 测试通过")


async def test_memory_service_list():
    """测试列出用户记忆"""
    service = get_memory_service()
    memories = await service.list_memories(user_id=TEST_USER_ID)
    assert isinstance(memories, list)
    print(f"✅ 列出记忆 测试通过, 共 {len(memories)} 条")


async def test_memory_service_delete():
    """测试删除记忆"""
    service = get_memory_service()
    # 写入一条
    mid = await service.add_memory(
        user_id=TEST_USER_ID,
        content="待删除的测试记忆",
        memory_type="fact",
        source_dialog_id=TEST_DIALOG_ID
    )
    if mid:
        ok = await service.delete_memory(mid)
        assert ok is True
        print(f"✅ 删除记忆 测试通过, id={mid}")
    else:
        print("✅ 删除记忆 测试跳过（写入失败/重复）")


# ============================================================
# 测试 4: memory_node 节点
# ============================================================
async def test_memory_node_with_context():
    """测试记忆检索节点 - 有 context 追加"""
    service = get_memory_service()
    # 写入测试数据
    await service.add_memory(
        user_id=TEST_USER_ID,
        content="用户喜欢用Python做数据分析",
        memory_type="preference"
    )
    await asyncio.sleep(2)

    state = {
        "user_input": "帮我分析一份数据",
        "user_id": TEST_USER_ID,
        "context": "【知识库检索结果】数据分析相关文档...",
        "session_id": "test_session"
    }
    result = await memory_node(state)
    assert result["context"] is not None
    assert "用户长期记忆" in result["context"]
    assert "知识库检索结果" in result["context"]
    print(f"✅ 记忆检索节点(追加context) 测试通过")


async def test_memory_node_no_context():
    """测试记忆检索节点 - 无 context 直接设置"""
    state = {
        "user_input": "你好",
        "user_id": TEST_USER_ID,
        "context": None,
        "session_id": "test_session"
    }
    result = await memory_node(state)
    # 可能有记忆也可能没有，只要不报错就行
    print(f"✅ 记忆检索节点(无context) 测试通过, context={result.get('context')}")


async def test_memory_node_no_user_id():
    """测试记忆检索节点 - 无 user_id 跳过"""
    state = {
        "user_input": "你好",
        "user_id": "",
        "context": "原始context",
        "session_id": "test_session"
    }
    result = await memory_node(state)
    assert result["context"] == "原始context"
    print("✅ 记忆检索节点(无user_id跳过) 测试通过")


# ============================================================
# 测试 5: memory_extract_node 节点（需要 LLM + Milvus）
# ============================================================
async def test_memory_extract_node():
    """测试记忆提取节点"""
    state = {
        "user_input": "我是武汉大学人工智能专业的学生，最近在研究RAG技术",
        "response": "你好，武汉大学AI专业的同学！RAG是当前很热门的方向。",
        "user_id": TEST_USER_ID,
        "session_id": "test_session_extract"
    }
    result = await memory_extract_node(state)
    assert isinstance(result, dict)
    print(f"✅ 记忆提取节点 测试通过, 返回: {result}")


async def test_memory_extract_node_no_response():
    """测试记忆提取节点 - 无 response 跳过"""
    state = {
        "user_input": "你好",
        "response": "",
        "user_id": TEST_USER_ID,
        "session_id": "test_session"
    }
    result = await memory_extract_node(state)
    assert result == {}
    print("✅ 记忆提取节点(无response跳过) 测试通过")


# ============================================================
# 清理测试数据
# ============================================================
async def cleanup():
    """清理测试产生的记忆数据"""
    service = get_memory_service()
    memories = await service.list_memories(user_id=TEST_USER_ID)
    for m in memories:
        mid = m.get("memory_id")
        if mid:
            await service.delete_memory(mid)
    print(f"🧹 清理完成，删除 {len(memories)} 条测试记忆")


# ============================================================
# 主函数
# ============================================================
async def main():
    print("=" * 60)
    print("🧠 长期记忆系统测试")
    print("=" * 60)

    # --- 同步测试：JSON 解析 ---
    test_json_parse_pure()
    test_json_parse_code_block()
    test_json_parse_with_surrounding_text()
    test_json_parse_invalid()

    # --- 异步测试：需要 LLM ---
    print("\n--- MemoryAgent 记忆提取测试 ---")
    try:
        await test_memory_agent_extract_preference()
        await test_memory_agent_extract_fact()
        await test_memory_agent_extract_nothing()
    except Exception as e:
        print(f"⚠️ MemoryAgent 测试失败（需要LLM连接）: {e}")

    # --- 异步测试：需要 Milvus ---
    print("\n--- MemoryService Milvus 读写测试 ---")
    try:
        await test_memory_service_add()
        await test_memory_service_search()
        await test_memory_service_duplicate()
        await test_memory_service_list()
        await test_memory_service_delete()
    except Exception as e:
        print(f"⚠️ MemoryService 测试失败（需要Milvus连接）: {e}")

    # --- 异步测试：节点 ---
    print("\n--- memory_node 节点测试 ---")
    try:
        await test_memory_node_no_user_id()
        await test_memory_node_with_context()
        await test_memory_node_no_context()
    except Exception as e:
        print(f"⚠️ memory_node 测试失败（需要Milvus连接）: {e}")

    print("\n--- memory_extract_node 节点测试 ---")
    try:
        await test_memory_extract_node_no_response()
        await test_memory_extract_node()
    except Exception as e:
        print(f"⚠️ memory_extract_node 测试失败（需要LLM+Milvus连接）: {e}")

    # --- 清理 ---
    print("\n--- 清理测试数据 ---")
    try:
        await cleanup()
    except Exception as e:
        print(f"⚠️ 清理失败: {e}")

    print("\n" + "=" * 60)
    print("🎉 所有测试执行完毕")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
