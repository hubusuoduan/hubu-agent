"""工具调用功能测试脚本"""
import asyncio
from loguru import logger

from app.tools import AgentTools, AgentToolsWithName
from app.config import settings


async def test_get_weather():
    """测试天气查询工具"""
    logger.info("=== 测试天气查询工具 ===")
    tool = AgentToolsWithName.get("get_weather")
    if not tool:
        logger.error("未找到天气查询工具")
        return
    
    # 测试有效城市
    try:
        result = await tool.ainvoke({"city": "北京"})
        logger.info(f"北京天气查询结果:\n{result}")
    except Exception as e:
        logger.error(f"天气查询工具测试失败: {e}")


async def test_web_search():
    """测试网络搜索工具"""
    logger.info("=== 测试网络搜索工具 ===")
    tool = AgentToolsWithName.get("web_search")
    if not tool:
        logger.error("未找到网络搜索工具")
        return
    
    # 测试搜索
    try:
        result = await tool.ainvoke({"query": "Python FastAPI教程", "max_results": 3})
        logger.info(f"网络搜索结果:\n{result}")
    except Exception as e:
        logger.error(f"网络搜索工具测试失败: {e}")


async def test_config():
    """测试配置文件"""
    logger.info("=== 测试工具配置 ===")
    
    weather_key = getattr(settings, 'WEATHER_API_KEY', '')
    tavily_key = getattr(settings, 'TAVILY_API_KEY', '')
    
    if not weather_key:
        logger.warning("WEATHER_API_KEY未配置，天气查询工具将返回提示信息")
    else:
        logger.info("WEATHER_API_KEY已配置")
    
    if not tavily_key:
        logger.warning("TAVILY_API_KEY未配置，网络搜索工具将返回提示信息")
    else:
        logger.info("TAVILY_API_KEY已配置")


async def main():
    """主测试函数"""
    logger.info("开始测试工具调用功能")
    
    # 测试配置
    await test_config()
    
    # 测试工具
    await test_get_weather()
    await test_web_search()
    
    logger.info("工具调用功能测试完成")


if __name__ == "__main__":
    asyncio.run(main())