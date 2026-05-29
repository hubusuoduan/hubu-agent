"""网页内容提取工具 - 从给定URL中提取纯文本内容"""
import requests
from bs4 import BeautifulSoup
from loguru import logger
from langchain.tools import tool

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

STRIP_TAGS = {"script", "style", "noscript", "iframe", "svg", "canvas", "template"}


@tool(parse_docstring=True)
def web_scraper(url: str, max_length: int = 5000) -> str:
    """提取网页中的纯文本内容。当需要读取某个网页链接的详细内容时调用此工具。

    Args:
        url: 要提取内容的网页URL地址，必须是完整的URL（如 https://example.com）。
        max_length: 返回内容的最大字符数，默认为5000。

    Returns:
        str: 网页中提取的纯文本内容，包括标题和正文。
    """
    if not url or not url.strip():
        return "URL不能为空"

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return f"无效的URL格式: {url}，URL必须以 http:// 或 https:// 开头"

    try:
        response = requests.get(url=url, headers=DEFAULT_HEADERS, timeout=15, allow_redirects=True)
        response.raise_for_status()

        if response.encoding and response.encoding.lower() != "iso-8859-1":
            encoding = response.encoding
        else:
            encoding = response.apparent_encoding or "utf-8"

        html_content = response.content.decode(encoding, errors="replace")
        soup = BeautifulSoup(html_content, "lxml")

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        for tag in soup.find_all(STRIP_TAGS):
            tag.decompose()

        content = _extract_main_content(soup)

        if not content.strip():
            return f"网页 {url} 中未提取到有效文本内容"

        if len(content) > max_length:
            content = content[:max_length] + f"\n\n... (内容已截断，当前显示前 {max_length} 字符)"

        result_parts = []
        if title:
            result_parts.append(f"📄 标题: {title}")
        result_parts.append(f"🔗 来源: {url}")
        result_parts.append(f"\n{'─' * 40}\n")
        result_parts.append(content)
        return "\n".join(result_parts)

    except requests.exceptions.Timeout:
        return f"访问网页超时: {url}，请稍后重试"
    except requests.exceptions.ConnectionError:
        return f"无法连接到网页: {url}，请检查URL是否正确"
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "未知"
        return f"网页请求失败 (HTTP {status_code}): {url}"
    except requests.exceptions.RequestException as e:
        return f"访问网页失败: {str(e)}"
    except Exception as e:
        logger.error(f"网页内容提取工具执行错误: {url}, 错误: {e}")
        return f"网页内容提取错误: {str(e)}"


def _extract_main_content(soup: BeautifulSoup) -> str:
    """从BeautifulSoup对象中智能提取正文内容"""
    # 策略1: 优先提取语义化标签
    for tag_name in ["article", "main"]:
        tag = soup.find(tag_name)
        if tag:
            text = _clean_text(tag.get_text(separator="\n", strip=True))
            if len(text) > 100:
                return text

    # 策略2: 查找包含最多文本的容器div/section
    best_text = ""
    best_length = 0
    for tag_name in ["section", "div"]:
        for tag in soup.find_all(tag_name):
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
        return best_text

    # 策略3: 回退到body整体文本
    body = soup.find("body")
    if body:
        return _clean_text(body.get_text(separator="\n", strip=True))

    return _clean_text(soup.get_text(separator="\n", strip=True))


def _clean_text(text: str) -> str:
    """清理提取的文本：去除多余空行和空白字符"""
    lines = text.split("\n")
    return "\n".join(line.strip() for line in lines if line.strip())
