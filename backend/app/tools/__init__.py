"""工具模块统一管理"""
from app.tools.get_weather.action import get_weather
from app.tools.web_search.action import web_search
from app.tools.web_scraper.action import web_scraper
from app.tools.knowledge_search.action import knowledge_search
from app.tools.knowledge_list.action import knowledge_list
from app.tools.code_runner.action import code_runner
from app.tools.report_generator.action import report_generator
from app.tools.chart_generator.action import chart_generator


# 所有可用工具列表
AgentTools = [
    get_weather,
    web_search,
    web_scraper,
    knowledge_search,
    knowledge_list,
    code_runner,
    report_generator,
    chart_generator,
]


# 工具字典，通过名称获取工具
AgentToolsWithName = {
    "get_weather": get_weather,
    "web_search": web_search,
    "web_scraper": web_scraper,
    "knowledge_search": knowledge_search,
    "knowledge_list": knowledge_list,
    "code_runner": code_runner,
    "report_generator": report_generator,
    "chart_generator": chart_generator,
}


__all__ = ["AgentTools", "AgentToolsWithName"]
