"""网络搜索工具"""
import requests
from loguru import logger
from langchain.tools import tool

from app.config import settings


@tool(parse_docstring=True)
def web_search(query: str, max_results: int = 5) -> str:
    """
    在网络上搜索信息。

    Args:
        query (str): 搜索关键词。
        max_results (int): 返回结果数量，默认为5。

    Returns:
        str: 搜索结果摘要。
    """
    return _search_web(query, max_results)


def _search_web(query: str, max_results: int = 5) -> str:
    """执行网络搜索"""
    api_key = getattr(settings, 'TAVILY_API_KEY', '')
    
    if not api_key:
        # 如果没有配置Tavily，返回提示信息
        return f"网络搜索API Key未配置，请在.env文件中设置TAVILY_API_KEY。\n\n搜索关键词: {query}"
    
    # 使用Tavily搜索API
    url = "https://api.tavily.com/search"
    
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        result = res.json()
        
        # Tavily API 成功时不返回 status_code，直接检查 results
        if res.status_code != 200:
            return f"搜索失败: {result.get('detail', '未知错误')}"
        
        results = result.get('results', [])
        if not results:
            return f"未找到与'{query}'相关的搜索结果"
        
        # 构建搜索结果
        search_messages = []
        for idx, item in enumerate(results, 1):
            title = item.get('title', '')
            url = item.get('url', '')
            content = item.get('content', '')
            
            search_msg = f"{idx}. {title}\n   URL: {url}\n   内容摘要: {content[:200]}..."
            search_messages.append(search_msg)
        
        # 构建最终返回结果
        final_result = f"🔍 搜索结果 (关键词: {query})\n\n"
        final_result += "\n\n".join(search_messages)
        final_result += f"\n\n 提示: 共找到 {len(results)} 条相关结果"
        
        return final_result
        
    except requests.exceptions.Timeout:
        logger.error("网络搜索请求超时")
        return "网络搜索超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        logger.error(f"网络搜索请求失败: {e}")
        return f"网络搜索失败: {str(e)}"
    except Exception as e:
        logger.error(f"网络搜索工具执行错误: {e}")
        return f"网络搜索错误: {str(e)}"
