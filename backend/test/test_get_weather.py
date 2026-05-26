"""get_weather 工具简单测试 - 用 __main__ 直接运行"""
from unittest.mock import patch, MagicMock
from app.tools.get_weather.action import get_weather, _get_weather


def test_no_api_key():
    """测试未配置 API Key"""
    with patch("app.tools.get_weather.action.settings") as mock_settings:
        mock_settings.WEATHER_API_KEY = ""
        result = _get_weather("北京")
        assert "API Key未配置" in result
    print("✅ 未配置API Key 测试通过")


def test_api_success():
    """测试天气查询成功"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "1",
        "forecasts": [{
            "city": "北京市",
            "casts": [
                {
                    "date": "2025-01-01",
                    "daytemp": "5",
                    "nighttemp": "-3",
                    "dayweather": "晴",
                    "nightweather": "晴"
                },
                {
                    "date": "2025-01-02",
                    "daytemp": "3",
                    "nighttemp": "-5",
                    "dayweather": "多云",
                    "nightweather": "阴"
                }
            ]
        }]
    }

    with patch("app.tools.get_weather.action.settings") as mock_settings,          patch("app.tools.get_weather.action.requests.get", return_value=mock_response) as mock_get:
        mock_settings.WEATHER_API_KEY = "test_key"
        mock_settings.WEATHER_API_ENDPOINT = "https://restapi.amap.com/v3/weather/forecast"
        result = _get_weather("北京")
        assert "北京市" in result
        assert "5°C" in result
        assert "晴" in result
        mock_get.assert_called_once()
    print("✅ 天气查询成功 测试通过")


def test_api_failure():
    """测试天气查询失败"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "0",
        "info": "INVALID_USER_KEY"
    }

    with patch("app.tools.get_weather.action.settings") as mock_settings,          patch("app.tools.get_weather.action.requests.get", return_value=mock_response):
        mock_settings.WEATHER_API_KEY = "invalid_key"
        mock_settings.WEATHER_API_ENDPOINT = "https://restapi.amap.com/v3/weather/forecast"
        result = _get_weather("北京")
        assert "查询失败" in result
    print("✅ 天气查询失败 测试通过")


def test_api_timeout():
    """测试天气查询超时"""
    import requests
    with patch("app.tools.get_weather.action.settings") as mock_settings,          patch("app.tools.get_weather.action.requests.get", side_effect=requests.exceptions.Timeout()):
        mock_settings.WEATHER_API_KEY = "test_key"
        mock_settings.WEATHER_API_ENDPOINT = "https://restapi.amap.com/v3/weather/forecast"
        result = _get_weather("北京")
        assert "超时" in result
    print("✅ 天气查询超时 测试通过")


def test_no_forecasts():
    """测试无天气预报数据"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "1",
        "forecasts": []
    }

    with patch("app.tools.get_weather.action.settings") as mock_settings,          patch("app.tools.get_weather.action.requests.get", return_value=mock_response):
        mock_settings.WEATHER_API_KEY = "test_key"
        mock_settings.WEATHER_API_ENDPOINT = "https://restapi.amap.com/v3/weather/forecast"
        result = _get_weather("未知城市")
        assert "未获取到天气数据" in result
    print("✅ 无天气预报数据 测试通过")


def test_tool_interface():
    """测试工具接口"""
    assert get_weather.name == "get_weather"
    assert "天气" in get_weather.description
    print("✅ 工具接口 测试通过")


if __name__ == "__main__":
    test_no_api_key()
    test_api_success()
    test_api_failure()
    test_api_timeout()
    test_no_forecasts()
    test_tool_interface()
    print("\n🎉 所有测试通过！")
