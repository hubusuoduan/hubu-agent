"""天气查询工具"""
import requests
from loguru import logger
from langchain.tools import tool

from app.config import settings


@tool(parse_docstring=True)
def get_weather(city: str) -> str:
    """
    查询用户提供城市的天气情况。当用户询问天气、气温、天气预报、穿衣建议、是否需要带伞等相关信息时调用此工具。

    Args:
        city (str): 用户提供的城市名称，例如：北京、上海、厦门、广州等。不要使用城市编码，直接使用中文城市名。

    Returns:
        str: 城市的天气信息，包括白天/夜间温度、天气状况（晴、雨、多云等）、日期等。
    
    Examples:
        - "今天天气怎么样？" -> 调用此工具
        - "厦门明天天气" -> 调用此工具
        - "北京需要带伞吗？" -> 调用此工具
        - "上海气温多少度？" -> 调用此工具
    """
    return _get_weather(city)


def _get_weather(location: str) -> str:
    """查询指定城市的天气信息"""
    api_key = getattr(settings, 'WEATHER_API_KEY', '')
    endpoint = getattr(settings, 'WEATHER_API_ENDPOINT', 'https://restapi.amap.com/v3/weather/forecast')
    
    if not api_key:
        return "天气查询API Key未配置，请在.env文件中设置WEATHER_API_KEY"
    
    params = {
        'key': api_key,
        'city': location,
        'extensions': 'all'
    }

    try:
        res = requests.get(url=endpoint, params=params, timeout=5)
        result = res.json()
        
        if result.get('status') != '1':
            return f"天气查询失败: {result.get('info', '未知错误')}"
        
        forecasts = result.get('forecasts', [])
        if not forecasts:
            return "未获取到天气数据"
        
        city_name = forecasts[0].get("city")
        casts = forecasts[0].get("casts", [])
        
        if not casts:
            return f"{city_name}暂无天气预报数据"
        
        # 构建天气信息
        weather_messages = []
        for item in casts:
            date = item.get('date')
            day_temp = item.get('daytemp')
            night_temp = item.get('nighttemp')
            day_weather = item.get('dayweather')
            night_weather = item.get('nightweather')
            
            weather_msg = f"📅 {date}: ️ 白天 {day_temp}°C / 夜间 {night_temp}°C | ☀️ 白天：{day_weather} | 🌙 夜间：{night_weather}"
            weather_messages.append(weather_msg)
        
        # 构建最终返回结果
        final_result = f"🌤️ {city_name} 地区天气信息\n\n"
        final_result += " 天气预报\n"
        final_result += "\n".join(weather_messages)
        final_result += "\n\n💡 温馨提示：天气数据仅供参考，请根据实际天气情况调整出行计划。"
        
        return final_result
        
    except requests.exceptions.Timeout:
        logger.error("天气查询请求超时")
        return "天气查询超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        logger.error(f"天气查询请求失败: {e}")
        return f"天气查询失败: {str(e)}"
    except Exception as e:
        logger.error(f"天气查询工具执行错误: {e}")
        return f"天气查询错误: {str(e)}"
