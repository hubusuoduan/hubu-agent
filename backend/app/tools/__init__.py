"""工具模块统一管理"""
from app.tools.get_weather.action import get_weather
from app.tools.web_search.action import web_search


# 所有可用工具列表
AgentTools = [
    get_weather,
    web_search,
]


# 工具字典，通过名称获取工具
AgentToolsWithName = {
    "get_weather": get_weather,
    "web_search": web_search,
}


__all__ = ["AgentTools", "AgentToolsWithName"]
