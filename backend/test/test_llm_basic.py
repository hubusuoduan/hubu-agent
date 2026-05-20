"""测试 LLM 基础功能"""
import asyncio
from app.services.llm_service import LLMService
from app.config import settings

async def test_llm_basic():
    print("="*60)
    print("测试 LLM 基础功能")
    print("="*60)
    
    # 初始化 LLM 模型
    print("\n步骤1: 初始化 LLM 模型")
    model = LLMService.get_model(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model_name=settings.LLM_MODEL
    )
    print(f"LLM 模型: {settings.LLM_MODEL}")
    print(f"Base URL: {settings.LLM_BASE_URL}")
    
    # 测试非流式调用
    print("\n步骤2: 测试非流式调用（invoke）\n")
    
    from langchain_core.messages import HumanMessage
    
    message = HumanMessage(content="你好")
    
    try:
        print("正在调用 LLM API...")
        response = await model.ainvoke([message])
        print(f"\n响应内容: {response.content}")
        print("\n" + "="*60)
        print("LLM API 调用成功！")
        print("="*60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n可能的问题:")
        print("1. API Key 不正确")
        print("2. Base URL 不可访问")
        print("3. 网络连接问题")
        print(f"4. 模型名称 '{settings.LLM_MODEL}' 可能不支持")

if __name__ == "__main__":
    asyncio.run(test_llm_basic())
