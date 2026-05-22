"""网页内容提取工具 - 从给定URL中提取纯文本内容"""
import requests
from bs4 import BeautifulSoup
from loguru import logger
from langchain.tools import tool

# 默认请求头，模拟浏览器访问
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 无意义标签，提取时直接移除
STRIP_TAGS = {"script", "style", "noscript", "iframe", "svg", "canvas", "template"}

# 正文内容标签，按优先级排序
CONTENT_TAGS = {"article", "main", "section", "div", "td"}

# 最大提取字符数
MAX_CONTENT_LENGTH = 8000


@tool(parse_docstring=True)
def web_scraper(url: str, max_length: int = 5000) -> str:
    """
    提取网页中的纯文本内容。当需要读取某个网页链接的详细内容时调用此工具，例如搜索结果中包含的URL链接、用户提供的网页地址等。

    Args:
        url (str): 要提取内容的网页URL地址，必须是完整的URL（如 https://example.com）。
        max_length (int): 返回内容的最大字符数，默认为5000。如果网页内容较长，会截断并提示。

    Returns:
        str: 网页中提取的纯文本内容，包括标题和正文。

    Examples:
        - "帮我看看这个链接说了什么 https://example.com" -> 调用此工具
        - "读取这个网页的内容" -> 调用此工具
        - "这个URL里有什么信息？" -> 调用此工具
    """
    return _scrape_web_page(url, max_length)


def _scrape_web_page(url: str, max_length: int = 5000) -> str:
    """执行网页内容提取"""

    # 基础URL校验
    if not url or not url.strip():
        return "URL不能为空"

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return f"无效的URL格式: {url}，URL必须以 http:// 或 https:// 开头"

    try:
        # 发送HTTP请求
        response = requests.get(
            url=url,
            headers=DEFAULT_HEADERS,
            timeout=15,
            allow_redirects=True,
        )
        response.raise_for_status()

        # 检测编码，优先使用响应头中的编码，回退到自动检测
        if response.encoding and response.encoding.lower() != "iso-8859-1":
            encoding = response.encoding
        else:
            encoding = response.apparent_encoding or "utf-8"

        html_content = response.content.decode(encoding, errors="replace")

        # 解析HTML
        soup = BeautifulSoup(html_content, "lxml")

        # 提取标题
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # 移除无意义标签
        for tag in soup.find_all(STRIP_TAGS):
            tag.decompose()

        # 提取正文内容
        content = _extract_main_content(soup)

        if not content.strip():
            return f"网页 {url} 中未提取到有效文本内容"

        # 截断过长内容
        if len(content) > max_length:
            content = content[:max_length]
            content += f"\n\n... (内容已截断，原始内容共 {len(content)} 字符，当前显示前 {max_length} 字符)"

        # 构建最终结果
        result_parts = []
        if title:
            result_parts.append(f"📄 标题: {title}")
        result_parts.append(f"🔗 来源: {url}")
        result_parts.append(f"\n{'─' * 40}\n")
        result_parts.append(content)

        final_result = "\n".join(result_parts)
        return final_result

    except requests.exceptions.Timeout:
        logger.error(f"网页请求超时: {url}")
        return f"访问网页超时: {url}，请稍后重试"
    except requests.exceptions.ConnectionError:
        logger.error(f"网页连接失败: {url}")
        return f"无法连接到网页: {url}，请检查URL是否正确"
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "未知"
        logger.error(f"网页请求HTTP错误: {url}, 状态码: {status_code}")
        return f"网页请求失败 (HTTP {status_code}): {url}"
    except requests.exceptions.RequestException as e:
        logger.error(f"网页请求失败: {url}, 错误: {e}")
        return f"访问网页失败: {str(e)}"
    except Exception as e:
        logger.error(f"网页内容提取工具执行错误: {url}, 错误: {e}")
        return f"网页内容提取错误: {str(e)}"


def _extract_main_content(soup: BeautifulSoup) -> str:
    """
    从BeautifulSoup对象中智能提取正文内容

    策略：
    1. 优先查找语义化标签（article, main）中的内容
    2. 如果没有语义标签，查找包含最多文本的div
    3. 最后回退到body整体文本

    Args:
        soup: BeautifulSoup对象

    Returns:
        提取的纯文本内容
    """
    # 策略1: 优先提取语义化标签
    for tag_name in ["article", "main"]:
        tag = soup.find(tag_name)
        if tag:
            text = _clean_text(tag.get_text(separator="\n", strip=True))
            if len(text) > 100:  # 确保有足够内容
                logger.debug(f"从 <{tag_name}> 标签提取到 {len(text)} 字符")
                return text

    # 策略2: 查找包含最多文本的容器div/section
    best_text = ""
    best_length = 0
    for tag_name in ["section", "div"]:
        for tag in soup.find_all(tag_name):
            # 跳过导航、页脚等区域
            tag_classes = " ".join(tag.get("class", []))
            tag_id = tag.get("id", "")
            skip_keywords = ["nav", "header", "footer", "sidebar", "comment", "ad", "menu", "banner"]
            if any(kw in tag_classes.lower() or kw in tag_id.lower() for kw in skip_keywords):
                continue

            text = _clean_text(tag.get_text(separator="\n", strip=True))
            if len(text) > best_length and len(text) > 200:
                best_text = text
                best_length = len(text)

    if best_length > 200:
        logger.debug(f"从容器标签提取到 {best_length} 字符")
        return best_text

    # 策略3: 回退到body整体文本
    body = soup.find("body")
    if body:
        text = _clean_text(body.get_text(separator="\n", strip=True))
        logger.debug(f"从body回退提取到 {len(text)} 字符")
        return text

    # 最终回退: 整个文档文本
    text = _clean_text(soup.get_text(separator="\n", strip=True))
    return text


def _clean_text(text: str) -> str:
    """
    清理提取的文本：去除多余空行和空白字符

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)
