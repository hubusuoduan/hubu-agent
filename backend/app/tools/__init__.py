"""工具模块统一管理"""
from app.tools.get_weather.action import get_weather
from app.tools.web_search.action import web_search
from app.tools.web_scraper.action import web_scraper
from app.tools.knowledge_search.action import knowledge_search
from app.tools.knowledge_list.action import knowledge_list
from app.tools.code_exec.action import code_exec
from app.tools.run_script.action import run_script
from app.tools.skill_loader.action import list_skills, load_skill, list_skill_resources, read_skill_resource
from app.tools.file_manager.action import (
    file_write, file_write_bytes, file_read, file_read_bytes,
    file_list, file_delete, file_move, file_mkdir,
    file_exists, file_info,
)
from app.tools.package_installer.action import (
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
    code_exec,
    run_script,
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
    "code_exec": code_exec,
    "run_script": run_script,
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


__all__ = ["AgentTools", "AgentToolsWithName"]
