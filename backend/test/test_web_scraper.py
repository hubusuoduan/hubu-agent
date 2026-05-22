"""web_scraper 工具简单测试 - 用 __main__ 直接运行"""
from app.tools.web_scraper.action import web_scraper, _scrape_web_page, _clean_text, _extract_main_content
from bs4 import BeautifulSoup


def test_clean_text():
    """测试文本清理"""
    assert _clean_text("  第一行  \n  第二行  ") == "第一行\n第二行"
    assert _clean_text("") == ""
    print("✅ _clean_text 测试通过")


def test_extract_main_content():
    """测试正文提取 - article标签优先"""
    html = """
    <html><body>
        <nav>导航栏内容</nav>
        <article>
            这是一篇很长的文章内容，包含了足够多的文字来满足最小长度要求。
            文章的正文应该被优先提取出来，而不是导航或者侧边栏的内容。
            继续添加更多内容以确保超过100字符的阈值限制。
            这样才能确保article标签的内容被正确识别和提取。
        </article>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = _extract_main_content(soup)
    assert "这是一篇很长的文章内容" in result
    assert "导航栏内容" not in result
    print("✅ _extract_main_content 测试通过")


def test_url_validation():
    """测试URL校验"""
    assert "URL不能为空" in _scrape_web_page("")
    assert "无效的URL格式" in _scrape_web_page("www.example.com")
    print("✅ URL校验 测试通过")


def test_tool_interface():
    """测试工具接口"""
    assert web_scraper.name == "web_scraper"
    assert "网页" in web_scraper.description or "提取" in web_scraper.description
    print("✅ 工具接口 测试通过")


if __name__ == "__main__":
    test_clean_text()
    test_extract_main_content()
    test_url_validation()
    test_tool_interface()
    print("\n🎉 所有测试通过！")
