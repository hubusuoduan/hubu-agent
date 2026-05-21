"""测试对话历史管理节点功能"""
import asyncio
from app.core.agents.summary_agent import SummaryAgent
from app.core.graph.nodes.history_node import history_manager_node
from app.services.llm_service import LLMService
from app.config import settings
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage


async def test_summary_agent():
    """测试摘要Agent功能"""
    print("\n" + "="*50)
    print("测试 SummaryAgent")
    print("="*50)
    
    # 创建模型实例
    model = LLMService.get_model(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model_name=settings.LLM_MODEL
    )
    
    # 创建摘要Agent
    summary_agent = SummaryAgent(model=model)
    
    # 模拟对话历史
    messages = [
        {"role": "user", "content": "你好，我想了解一下机器学习的基础知识"},
        {"role": "assistant", "content": "机器学习是人工智能的一个分支，主要研究如何让计算机从数据中学习..."},
        {"role": "user", "content": "那深度学习呢？"},
        {"role": "assistant", "content": "深度学习是机器学习的一个子领域，使用多层神经网络..."},
        {"role": "user", "content": "它们之间有什么区别？"},
        {"role": "assistant", "content": "主要区别在于：1. 数据需求不同 2. 硬件要求不同 3. 可解释性..."},
        {"role": "user", "content": "我想学习深度学习，有什么推荐的资源吗？"},
        {"role": "assistant", "content": "推荐以下资源：1. 《深度学习》花书 2. Coursera的深度学习课程..."},
        {"role": "user", "content": "这些资源是免费的吗？"},
        {"role": "assistant", "content": "部分是免费的，Coursera可以申请助学金..."},
    ]
    
    # 生成摘要
    summary = await summary_agent.summarize(messages)
    
    if summary:
        print("\n生成的摘要：")
        print("-" * 50)
        print(summary)
        print("-" * 50)
        print(f"摘要长度: {len(summary)} 字符")
    else:
        print("\n摘要生成失败")


async def test_history_manager_node():
    """测试历史管理节点功能"""
    print("\n" + "="*50)
    print("测试 History Manager Node")
    print("="*50)
    
    # 模拟大量对话历史
    messages = []
    for i in range(30):  # 30轮对话
        messages.append(HumanMessage(content=f"用户问题 {i+1}"))
        messages.append(AIMessage(content=f"助手回答 {i+1}"))
    
    print(f"\n原始消息数量: {len(messages)}")
    
    # 构建 state
    state = {
        "messages": messages,
        "user_input": "测试输入",
        "context": None,
        "session_id": "test_session",
        "response": ""
    }
    
    # 执行历史管理节点
    result = await history_manager_node(state)
    
    print(f"压缩后消息数量: {len(result.get('messages', []))}")
    
    # 检查是否包含摘要
    if result.get('messages'):
        first_msg = result['messages'][0]
        if hasattr(first_msg, 'type') and first_msg.type == 'system':
            print("\n包含摘要，摘要内容：")
            print("-" * 50)
            print(first_msg.content)
            print("-" * 50)


async def main():
    """主测试函数"""
    logger.info("开始测试对话历史管理节点功能")
    
    try:
        # 测试摘要Agent
        await test_summary_agent()
        
        # 测试历史管理节点
        await test_history_manager_node()
        
        print("\n" + "="*50)
        print("所有测试完成！")
        print("="*50)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
