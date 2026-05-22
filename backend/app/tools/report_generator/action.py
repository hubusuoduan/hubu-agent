"""报告生成工具 - 将内容生成为可下载的报告文件"""
import os
from datetime import datetime
from loguru import logger
from langchain.tools import tool

from app.config import settings

# 报告文件存储目录
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "reports")

# 支持的文件格式
SUPPORTED_FORMATS = {"markdown", "txt", "html"}

# 最大内容长度
MAX_CONTENT_LENGTH = 100000


@tool(parse_docstring=True)
async def report_generator(title: str, content: str, file_format: str = "markdown") -> str:
    """
    生成报告文件并返回下载信息。当用户需要将内容保存为文件、生成报告、导出文档时调用此工具。支持 Markdown、纯文本和 HTML 格式。

    Args:
        title (str): 报告标题，将用作文件名（自动清理非法字符）。
        content (str): 报告内容，支持 Markdown 格式文本。
        file_format (str): 文件格式，可选 "markdown"、"txt"、"html"，默认为 "markdown"。

    Returns:
        str: 报告生成结果，包含报告ID、文件名和下载链接。

    Examples:
        - "帮我生成一份周报" -> 调用此工具，title="本周工作周报"，content=报告内容
        - "把这段内容导出为文件" -> 调用此工具
        - "生成一份HTML格式的分析报告" -> 调用此工具，file_format="html"
    """
    return await _generate_report(title, content, file_format)


async def _generate_report(title: str, content: str, file_format: str = "markdown") -> str:
    """执行报告生成"""

    # 参数校验
    if not title or not title.strip():
        return "报告标题不能为空"

    title = title.strip()

    if not content or not content.strip():
        return "报告内容不能为空"

    # 限制内容长度
    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH]
        logger.warning(f"报告内容超过最大长度{MAX_CONTENT_LENGTH}，已截断")

    # 格式校验
    file_format = file_format.strip().lower()
    if file_format not in SUPPORTED_FORMATS:
        formats_str = "、".join(SUPPORTED_FORMATS)
        return f"不支持的文件格式: {file_format}，支持的格式: {formats_str}"

    try:
        # 生成文件名和路径
        file_name, file_path = _build_file_path(title, file_format)

        # 根据格式处理内容
        file_content = _format_content(title, content, file_format)

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        file_size = os.path.getsize(file_path)

        # 保存记录到数据库
        report_id = await _save_report_record(title, file_name, file_path, file_format, file_size)

        # 构建下载链接
        download_url = f"/api/v1/report/download/{report_id}"

        # 构建返回结果
        result_parts = [
            f"📄 报告生成成功！",
            f"📋 标题: {title}",
            f"📁 文件名: {file_name}",
            f"📦 格式: {file_format}",
            f"💾 大小: {file_size} 字节",
            f"🔗 下载链接: {download_url}",
            "💡 用户可通过下载链接获取报告文件",
        ]

        return "\n".join(result_parts)

    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        return f"报告生成失败: {str(e)}"


def _build_file_path(title: str, file_format: str) -> tuple:
    """构建文件名和存储路径"""
    # 清理标题中的非法文件名字符
    safe_title = title
    for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        safe_title = safe_title.replace(char, '_')

    # 限制文件名长度
    if len(safe_title) > 100:
        safe_title = safe_title[:100]

    # 日期目录
    date_dir = datetime.now().strftime("%Y%m")

    # 扩展名映射
    ext_map = {
        "markdown": ".md",
        "txt": ".txt",
        "html": ".html",
    }
    ext = ext_map.get(file_format, ".md")

    # 时间戳后缀避免重名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{safe_title}_{timestamp}{ext}"

    # 完整路径
    file_path = os.path.join(REPORT_DIR, date_dir, file_name)

    return file_name, file_path


def _format_content(title: str, content: str, file_format: str) -> str:
    """根据格式处理内容"""
    if file_format == "markdown":
        # Markdown: 添加标题和时间戳
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"# {title}\n\n> 生成时间: {now}\n\n---\n\n{content}"

    elif file_format == "txt":
        # 纯文本: 去除 Markdown 格式标记
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_content = _strip_markdown(content)
        return f"{title}\n{'=' * len(title.encode('gbk', errors='replace'))}\n生成时间: {now}\n{'-' * 40}\n\n{clean_content}"

    elif file_format == "html":
        # HTML: 将 Markdown 转为简单 HTML
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_body = _markdown_to_html(content)
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.8;
            color: #333;
            background: #fafafa;
        }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #4a9eff; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 1.5em; }}
        h3 {{ color: #34495e; }}
        blockquote {{
            border-left: 4px solid #4a9eff;
            margin: 1em 0;
            padding: 0.5em 1em;
            background: #f0f7ff;
            color: #555;
        }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
        pre {{ background: #2d2d2d; color: #f8f8f2; padding: 16px; border-radius: 6px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; color: inherit; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 2em 0; }}
        .meta {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="meta">生成时间: {now}</p>
    <hr>
    {html_body}
</body>
</html>"""

    return content


def _strip_markdown(text: str) -> str:
    """简单去除 Markdown 格式标记"""
    import re
    # 去除标题标记
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 去除加粗/斜体
    text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    # 去除链接，保留文本
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 去除图片
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # 去除代码块标记
    text = re.sub(r'```[\s\S]*?```', lambda m: m.group(0).replace('```', '').strip(), text)
    # 去除行内代码
    text = re.sub(r'`(.*?)`', r'\1', text)
    return text


def _markdown_to_html(text: str) -> str:
    """简单的 Markdown 转 HTML"""
    import re

    # 转义 HTML 特殊字符
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 代码块
    text = re.sub(
        r'```(\w*)\n([\s\S]*?)```',
        lambda m: f'<pre><code>{m.group(2)}</code></pre>',
        text
    )

    # 行内代码
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

    # 标题
    text = re.sub(r'^######\s+(.+)$', r'<h6>\1</h6>', text, flags=re.MULTILINE)
    text = re.sub(r'^#####\s+(.+)$', r'<h5>\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)

    # 加粗和斜体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # 链接
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)

    # 引用
    text = re.sub(r'^>\s+(.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)

    # 分割线
    text = re.sub(r'^---+$', '<hr>', text, flags=re.MULTILINE)

    # 无序列表
    text = re.sub(r'^[\s]*[-*+]\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)

    # 段落（简单处理：双换行分段）
    text = re.sub(r'\n\n', '</p>\n<p>', text)

    # 包裹段落标签
    text = f'<p>{text}</p>'

    # 清理空段落
    text = re.sub(r'<p>\s*</p>', '', text)

    return text


async def _save_report_record(title: str, file_name: str, file_path: str, file_format: str, file_size: int) -> str:
    """保存报告记录到数据库"""
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.database.engine import async_engine
    from app.database.models.report import ReportTable, ReportStatus

    if async_engine is None:
        # 数据库未连接，返回临时ID
        import hashlib
        return hashlib.md5(file_path.encode()).hexdigest()[:16]

    async with AsyncSession(async_engine) as session:
        report = ReportTable(
            title=title,
            file_name=file_name,
            file_path=file_path,
            file_format=file_format,
            file_size=file_size,
            status=ReportStatus.COMPLETED,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report.id
