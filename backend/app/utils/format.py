"""格式化工具函数"""
from typing import Dict


def fmt_size(size: int) -> str:
    """格式化文件大小

    Args:
        size: 文件大小（字节）

    Returns:
        格式化后的字符串，如 '1.5MB'
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}" if unit != "B" else f"{size}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


# 工具名称中文映射
TOOL_DISPLAY_NAMES: Dict[str, str] = {
    "get_weather": "天气查询",
    "web_search": "网络搜索",
    "web_scraper": "网页抓取",
    "knowledge_search": "知识库搜索",
    "knowledge_list": "知识库列表",
    "code_runner": "沙箱代码执行",
    "code_exec": "代码执行",
    "load_skill": "加载技能",
    "list_skill_resources": "列出技能资源",
    "read_skill_resource": "读取技能资源",
    "file_write": "写入文件",
    "file_write_bytes": "写入二进制文件",
    "file_read": "读取文件",
    "file_read_bytes": "读取二进制文件",
    "file_list": "文件列表",
    "file_delete": "删除文件",
    "file_move": "移动文件",
    "file_mkdir": "创建目录",
    "file_exists": "检查文件",
    "file_info": "文件信息",
    "pip_install": "安装Python包",
    "npm_install": "安装NPM包",
    "pip_check": "检查Python包",
    "npm_check": "检查NPM包",
    "pip_list": "列出Python包",
    "npm_list": "列出NPM包",
}


def format_tool_display_name(tool_name: str) -> str:
    """将工具内部名称格式化为友好的显示名称

    Args:
        tool_name: 工具内部名称

    Returns:
        友好的显示名称
    """
    return TOOL_DISPLAY_NAMES.get(tool_name, tool_name)
