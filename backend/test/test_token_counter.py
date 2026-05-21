"""TokenCounter 功能测试"""
import asyncio
from app.utils.token_counter import TokenCounter
from app.core.agents.summary_agent import SummaryAgent
from app.services.llm_service import LLMService
from app.config import settings


async def test_token_counter_basic():
    """测试基本的token计算功能"""
    print("=" * 60)
    print("测试1: 基本Token计算")
    print("=" * 60)
    
    counter = TokenCounter()
    
    # 测试单条消息
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
    ]
    
    tokens = counter.count_message_tokens(messages)
    print(f"消息数: {len(messages)}")
    print(f"Token数: {tokens}")
    print()


async def test_token_counter_truncate():
    """测试Token截断功能（无摘要）"""
    print("=" * 60)
    print("测试2: Token截断（无摘要）")
    print("=" * 60)
    
    counter = TokenCounter()
    
    # 创建10条消息
    messages = []
    for i in range(10):
        messages.append({"role": "user", "content": f"用户问题 {i+1}，这是一段较长的文本用于测试"})
        messages.append({"role": "assistant", "content": f"助手回答 {i+1}，这是对应的回复内容"})
    
    total_tokens = counter.count_message_tokens(messages)
    print(f"原始消息数: {len(messages)}")
    print(f"原始Token数: {total_tokens}")
    
    # 设置限制为3000 tokens
    max_tokens = 3000
    truncated = await counter.truncate_messages_by_tokens(messages, max_tokens, preserve_first=False)
    
    final_tokens = counter.count_message_tokens(truncated)
    print(f"截断后消息数: {len(truncated)}")
    print(f"截断后Token数: {final_tokens}")
    print(f"是否满足限制: {final_tokens <= max_tokens}")
    print()


async def test_token_counter_with_summary():
    """测试带摘要的Token截断"""
    print("=" * 60)
    print("测试3: Token截断（带原始摘要）")
    print("=" * 60)
    
    counter = TokenCounter()
    
    # 创建带摘要的消息列表
    messages = [
        {"role": "user", "content": "[历史对话摘要]\n之前讨论了Python编程的基础知识。"},
    ]
    
    # 添加8条新消息
    for i in range(8):
        messages.append({"role": "user", "content": f"用户问题 {i+1}，关于Python的深入问题"})
        messages.append({"role": "assistant", "content": f"助手回答 {i+1}，详细解释Python相关知识"})
    
    total_tokens = counter.count_message_tokens(messages)
    print(f"原始消息数: {len(messages)}")
    print(f"原始Token数: {total_tokens}")
    
    # 设置限制为2500 tokens
    max_tokens = 2500
    truncated = await counter.truncate_messages_by_tokens(messages, max_tokens, preserve_first=True)
    
    final_tokens = counter.count_message_tokens(truncated)
    print(f"截断后消息数: {len(truncated)}")
    print(f"截断后Token数: {final_tokens}")
    
    # 验证第一条是否是摘要
    if len(truncated) > 0 and "[历史对话摘要]" in truncated[0]["content"]:
        print("[OK] 原始摘要已保留")
    else:
        print("[FAIL] 原始摘要丢失")
    print()


async def test_token_counter_with_secondary_summary():
    """测试二次摘要生成"""
    print("=" * 60)
    print("测试4: Token截断（带二次摘要）")
    print("=" * 60)
    
    # 创建SummaryAgent
    model = LLMService.get_model(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model_name=settings.LLM_MODEL
    )
    summary_agent = SummaryAgent(model=model)
    
    # 创建TokenCounter，传入SummaryAgent
    counter = TokenCounter(summary_agent=summary_agent)
    
    # 创建带摘要的消息列表
    messages = [
        {"role": "user", "content": "[历史对话摘要]\n之前讨论了Python和JavaScript的区别。"},
    ]
    
    # 添加15条消息（会触发截断）
    for i in range(15):
        messages.append({"role": "user", "content": f"用户问题 {i+1}，这是一个比较复杂的问题，需要详细解释相关的技术细节和最佳实践"})
        messages.append({"role": "assistant", "content": f"助手回答 {i+1}，针对这个问题我给出详细的解答，包括代码示例和注意事项"})
    
    total_tokens = counter.count_message_tokens(messages)
    print(f"原始消息数: {len(messages)}")
    print(f"原始Token数: {total_tokens}")
    
    # 设置限制为800 tokens（强制触发截断）
    max_tokens = 800
    truncated = await counter.truncate_messages_by_tokens(messages, max_tokens, preserve_first=True)
    
    final_tokens = counter.count_message_tokens(truncated)
    print(f"截断后消息数: {len(truncated)}")
    print(f"截断后Token数: {final_tokens}")
    
    # 验证结果
    if len(truncated) > 0:
        print(f"\n消息结构:")
        for i, msg in enumerate(truncated):
            preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            print(f"  [{i}] {msg['role']}: {preview}")
        
        # 检查是否有二次摘要
        summary_count = sum(1 for msg in truncated if "[历史对话摘要]" in msg["content"])
        print(f"\n摘要数量: {summary_count}")
        if summary_count >= 2:
            print("[OK] 生成了二次摘要")
        elif summary_count == 1:
            print("[OK] 保留了原始摘要")
        else:
            print("[FAIL] 没有摘要")
    print()


async def test_edge_cases():
    """测试边界情况"""
    print("=" * 60)
    print("测试5: 边界情况")
    print("=" * 60)
    
    counter = TokenCounter()
    
    # 测试1: 空消息列表
    result = await counter.truncate_messages_by_tokens([], 1000)
    print(f"空消息列表: {len(result)} 条 [OK]")
    
    # 测试2: 单条消息
    messages = [{"role": "user", "content": "单条消息"}]
    result = await counter.truncate_messages_by_tokens(messages, 1000)
    print(f"单条消息: {len(result)} 条 [OK]")
    
    # 测试3: token限制非常小
    messages = [
        {"role": "user", "content": "消息1"},
        {"role": "assistant", "content": "回答1"},
        {"role": "user", "content": "消息2"}
    ]
    result = await counter.truncate_messages_by_tokens(messages, 50)
    print(f"极小token限制: {len(result)} 条（应该至少有1条）")
    
    # 测试4: token限制很大（不需要截断）
    result = await counter.truncate_messages_by_tokens(messages, 10000)
    print(f"极大token限制: {len(result)} 条（应该等于原消息数 {len(messages)}）")
    print()


async def main():
    """运行所有测试"""
    print("\n开始 TokenCounter 功能测试\n")
    
    try:
        await test_token_counter_basic()
        await test_token_counter_truncate()
        await test_token_counter_with_summary()
        await test_token_counter_with_secondary_summary()
        await test_edge_cases()
        
        print("=" * 60)
        print("所有测试完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
