"""工具模块统一管理"""
from app.tools.get_weather import get_weather
from app.tools.web_search import web_search
from app.tools.web_scraper import web_scraper
from app.tools.knowledge_search import knowledge_search
from app.tools.knowledge_list import knowledge_list
from app.tools.exec_python import exec_python
from app.tools.exec_js import exec_js
from app.tools.skill_loader import list_skills, load_skill, list_skill_resources, read_skill_resource
from app.tools.file_manager import (
    file_write, file_write_bytes, file_read, file_read_bytes,
    file_list, file_delete, file_move, file_mkdir,
    file_exists, file_info,
)
from app.tools.package_installer import (
    pip_install, npm_install, pip_check, npm_check,
    pip_list, npm_list,
)


# 所有可用工具列表
AgentTools = [
    get_weather,
    web_search,
    web_scraper,
    knowledge_search,
    knowledge_list,
    exec_python,
    exec_js,
    list_skills,
    load_skill,
    list_skill_resources,
    read_skill_resource,
    file_write,
    file_write_bytes,
    file_read,
    file_read_bytes,
    file_list,
    file_delete,
    file_move,
    file_mkdir,
    file_exists,
    file_info,
    pip_install,
    npm_install,
    pip_check,
    npm_check,
    pip_list,
    npm_list,
]


# 工具字典，通过名称获取工具
AgentToolsWithName = {
    "get_weather": get_weather,
    "web_search": web_search,
    "web_scraper": web_scraper,
    "knowledge_search": knowledge_search,
    "knowledge_list": knowledge_list,
    "exec_python": exec_python,
    "exec_js": exec_js,
    "list_skills": list_skills,
    "load_skill": load_skill,
    "list_skill_resources": list_skill_resources,
    "read_skill_resource": read_skill_resource,
    "file_write": file_write,
    "file_write_bytes": file_write_bytes,
    "file_read": file_read,
    "file_read_bytes": file_read_bytes,
    "file_list": file_list,
    "file_delete": file_delete,
    "file_move": file_move,
    "file_mkdir": file_mkdir,
    "file_exists": file_exists,
    "file_info": file_info,
    "pip_install": pip_install,
    "npm_install": npm_install,
    "pip_check": pip_check,
    "npm_check": npm_check,
    "pip_list": pip_list,
    "npm_list": npm_list,
}


# ============================================================
# 按角色分组的工具列表
# ============================================================

# Chat Agent 工具 — 通用对话，不需要工具
ChatTools = []

# Researcher Agent 工具 — 信息检索
ResearcherTools = [
    web_search,
    web_scraper,
    knowledge_search,
    knowledge_list,
    get_weather,
]

# Coder Agent 工具 — 代码执行与文件管理
CoderTools = [
    exec_python,
    exec_js,
    file_write,
    file_write_bytes,
    file_read,
    file_read_bytes,
    file_list,
    file_delete,
    file_move,
    file_mkdir,
    file_exists,
    file_info,
    pip_install,
    npm_install,
    pip_check,
    npm_check,
    pip_list,
    npm_list,
]

# Skill Agent 工具 — 技能执行
SkillTools = [
    list_skills,
    load_skill,
    list_skill_resources,
    read_skill_resource,
    exec_python,
    exec_js,
    file_write,
    file_write_bytes,
    file_read,
    file_read_bytes,
    file_list,
    file_exists,
    file_mkdir,
    file_move,
    file_delete,
    pip_install,
    npm_install,
    pip_check,
    npm_check,
]


__all__ = ["AgentTools", "AgentToolsWithName", "ChatTools", "ResearcherTools", "CoderTools", "SkillTools"]
