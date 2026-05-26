"""web_search 工具简单测试 - 用 __main__ 直接运行"""
from unittest.mock import patch, MagicMock
from app.tools.web_search.action import web_search, _search_web


def test_no_api_key():
    """测试未配置 API Key"""
    with patch("app.tools.web_search.action.settings") as mock_settings:
        mock_settings.TAVILY_API_KEY = ""
        result = _search_web("Python教程")
        assert "API Key未配置" in result
        assert "Python教程" in result
    print("✅ 未配置API Key 测试通过")


def test_search_success():
    """测试搜索成功"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"title": "Python官方教程", "url": "https://docs.python.org", "content": "Python官方文档和教程"},
            {"title": "菜鸟教程Python", "url": "https://www.runoob.com/python", "content": "Python基础语法教程"},
        ]
    }

    with patch("app.tools.web_search.action.settings") as mock_settings,          patch("app.tools.web_search.action.requests.post", return_value=mock_response):
        mock_settings.TAVILY_API_KEY = "test_key"
        result = _search_web("Python教程")
        assert "Python官方教程" in result
        assert "docs.python.org" in result
        assert "2 条" in result
    print("✅ 搜索成功 测试通过")


def test_search_no_results():
    """测试搜索无结果"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    with patch("app.tools.web_search.action.settings") as mock_settings,          patch("app.tools.web_search.action.requests.post", return_value=mock_response):
        mock_settings.TAVILY_API_KEY = "test_key"
        result = _search_web("xyzabc123不存在的关键词")
        assert "未找到" in result
    print("✅ 搜索无结果 测试通过")


def test_search_api_error():
    """测试搜索API错误"""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"detail": "Invalid API key"}

    with patch("app.tools.web_search.action.settings") as mock_settings,          patch("app.tools.web_search.action.requests.post", return_value=mock_response):
        mock_settings.TAVILY_API_KEY = "invalid_key"
        result = _search_web("test")
        assert "搜索失败" in result
    print("✅ 搜索API错误 测试通过")


def test_search_timeout():
    """测试搜索超时"""
    import requests
    with patch("app.tools.web_search.action.settings") as mock_settings,          patch("app.tools.web_search.action.requests.post", side_effect=requests.exceptions.Timeout()):
        mock_settings.TAVILY_API_KEY = "test_key"
        result = _search_web("test")
        assert "超时" in result
    print("✅ 搜索超时 测试通过")


def test_tool_interface():
    """测试工具接口"""
    assert web_search.name == "web_search"
    assert "搜索" in web_search.description
    print("✅ 工具接口 测试通过")


if __name__ == "__main__":
    test_no_api_key()
    test_search_success()
    test_search_no_results()
    test_search_api_error()
    test_search_timeout()
    test_tool_interface()
    print("\n🎉 所有测试通过！")
