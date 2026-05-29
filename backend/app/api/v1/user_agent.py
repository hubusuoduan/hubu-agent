"""用户自建 Agent API"""
import os
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.database.session import get_async_session
from app.database.dao.user_agent_dao import UserAgentDao
from app.database.models.user_agent import UserAgentTable
from app.schemas.user_agent import (
    UserAgentCreate,
    UserAgentUpdate,
    UserAgentResponse,
    UserAgentListResponse,
    ToolListResponse,
    ToolInfo,
)
from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.tools import AgentToolsWithName

router = APIRouter(prefix="/user_agent", tags=["用户自建Agent"])

# AGENT.md 文件存放根目录
_CUSTOM_AGENTS_DIR = Path(__file__).parent.parent.parent / "core" / "agents" / "custom"

# 用户最多创建的 Agent 数量
MAX_USER_AGENTS = 10


def _build_agent_md(config: UserAgentCreate) -> str:
    """根据用户输入构建 AGENT.md 文件内容"""
    tools_str = ", ".join(config.tools) if config.tools else ""
    return f"""---
name: {config.name}
display_name: {config.display_name}
description: {config.description}
tools: [{tools_str}]
---

{config.system_prompt}"""


def _get_agent_dir(user_id: int, agent_name: str) -> Path:
    """获取用户 Agent 的存放目录"""
    return _CUSTOM_AGENTS_DIR / str(user_id) / agent_name


def _get_agent_path(user_id: int, agent_name: str) -> str:
    """获取 AGENT.md 的相对路径（存入数据库）"""
    return f"custom/{user_id}/{agent_name}/AGENT.md"


def _validate_agent_name(name: str) -> bool:
    """校验 Agent 名称合法性（防止路径穿越等安全问题）"""
    # 只允许字母、数字、下划线，且以字母开头
    if not name or not name[0].isalpha():
        return False
    if not all(c.isalnum() or c == "_" for c in name):
        return False
    # 防止路径穿越
    if ".." in name or "/" in name or "\\" in name:
        return False
    return True


def _validate_tools(tools: list) -> list:
    """校验工具名称是否在可用工具池中，返回合法的工具列表"""
    valid = []
    for tool_name in tools:
        if tool_name in AgentToolsWithName:
            valid.append(tool_name)
        else:
            logger.warning(f"忽略不存在的工具: {tool_name}")
    return valid


@router.post("/", response_model=UserAgentResponse, summary="创建用户自建Agent")
async def create_user_agent(
    data: UserAgentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """创建用户自建 Agent（写 AGENT.md + 写 MySQL）"""
    user_id = current_user.id

    # 校验名称合法性
    if not _validate_agent_name(data.name):
        raise HTTPException(status_code=400, detail="Agent名称不合法，只允许字母开头，包含字母、数字、下划线")

    # 校验名称不能和系统 Agent 冲突
    from app.core.agents.llm.supervisor_agent import SYSTEM_AGENTS
    if data.name in SYSTEM_AGENTS:
        raise HTTPException(status_code=400, detail=f"Agent名称不能和系统Agent冲突: {data.name}")

    # 校验工具列表
    valid_tools = _validate_tools(data.tools)

    # 检查数量上限
    existing = await UserAgentDao.get_all_by_user_id(user_id)
    if len(existing) >= MAX_USER_AGENTS:
        raise HTTPException(status_code=400, detail=f"每个用户最多创建 {MAX_USER_AGENTS} 个Agent")

    # 检查名称唯一性
    existing_agent = await UserAgentDao.get_by_user_and_name(user_id, data.name)
    if existing_agent:
        raise HTTPException(status_code=400, detail=f"Agent名称已存在: {data.name}")

    # 写 AGENT.md 文件
    agent_dir = _get_agent_dir(user_id, data.name)
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_md_path = agent_dir / "AGENT.md"

    # 构建 md 内容（用校验后的工具列表）
    create_data = UserAgentCreate(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        system_prompt=data.system_prompt,
        tools=valid_tools,
    )
    md_content = _build_agent_md(create_data)
    agent_md_path.write_text(md_content, encoding="utf-8")
    logger.info(f"写入 AGENT.md: {agent_md_path}")

    # 写 MySQL 索引
    agent_path = _get_agent_path(user_id, data.name)
    record = await UserAgentDao.create_agent(
        user_id=user_id,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        agent_path=agent_path,
    )

    return UserAgentResponse(
        id=record.id,
        user_id=record.user_id,
        name=record.name,
        display_name=record.display_name,
        description=record.description,
        tools=valid_tools,
        system_prompt=data.system_prompt,
        enabled=record.enabled,
        create_time=record.create_time,
        update_time=record.update_time,
    )


@router.get("/", response_model=UserAgentListResponse, summary="获取用户自建Agent列表")
async def list_user_agents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """获取当前用户的所有自建 Agent"""
    user_id = current_user.id
    records = await UserAgentDao.get_all_by_user_id(user_id)

    items = []
    for r in records:
        # 从 AGENT.md 读取工具列表
        tools = _read_tools_from_md(r.agent_path)
        items.append(UserAgentResponse(
            id=r.id,
            user_id=r.user_id,
            name=r.name,
            display_name=r.display_name,
            description=r.description,
            tools=tools,
            enabled=r.enabled,
            create_time=r.create_time,
            update_time=r.update_time,
        ))

    return UserAgentListResponse(total=len(items), items=items)


@router.get("/{agent_id}", response_model=UserAgentResponse, summary="获取用户自建Agent详情")
async def get_user_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """获取指定 Agent 的详情"""
    record = await UserAgentDao.get_by_id(agent_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agent不存在")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该Agent")

    config = _read_full_agent_md(record.agent_path)
    tools = config.get("tools", [])
    system_prompt = config.get("system_prompt", "")
    return UserAgentResponse(
        id=record.id,
        user_id=record.user_id,
        name=record.name,
        display_name=record.display_name,
        description=record.description,
        tools=tools,
        system_prompt=system_prompt,
        enabled=record.enabled,
        create_time=record.create_time,
        update_time=record.update_time,
    )


@router.put("/{agent_id}", response_model=UserAgentResponse, summary="更新用户自建Agent")
async def update_user_agent(
    agent_id: int,
    data: UserAgentUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """更新 Agent 信息（同时更新 AGENT.md 和 MySQL）"""
    record = await UserAgentDao.get_by_id(agent_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agent不存在")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改该Agent")

    # 读取现有 AGENT.md 获取当前配置
    existing_config = _read_full_agent_md(record.agent_path)

    # 合并更新字段
    display_name = data.display_name if data.display_name is not None else record.display_name
    description = data.description if data.description is not None else record.description
    system_prompt = data.system_prompt if data.system_prompt is not None else existing_config.get("system_prompt", "")
    tools = _validate_tools(data.tools) if data.tools is not None else existing_config.get("tools", [])

    # 更新 AGENT.md（去掉 agent_path 中的 custom/ 前缀）
    relative_path = record.agent_path
    if relative_path.startswith("custom/"):
        relative_path = relative_path[len("custom/"):]
    agent_md_path = _CUSTOM_AGENTS_DIR / relative_path
    md_content = f"""---
name: {record.name}
display_name: {display_name}
description: {description}
tools: [{", ".join(tools)}]
---

{system_prompt}"""
    agent_md_path.write_text(md_content, encoding="utf-8")

    # 更新 MySQL
    update_kwargs = {"display_name": display_name, "description": description}
    if data.enabled is not None:
        update_kwargs["enabled"] = data.enabled
    await UserAgentDao.update_agent(agent_id, **update_kwargs)

    # 重新读取记录
    record = await UserAgentDao.get_by_id(agent_id)

    return UserAgentResponse(
        id=record.id,
        user_id=record.user_id,
        name=record.name,
        display_name=record.display_name,
        description=record.description,
        tools=tools,
        system_prompt=system_prompt,
        enabled=record.enabled,
        create_time=record.create_time,
        update_time=record.update_time,
    )


@router.delete("/{agent_id}", summary="删除用户自建Agent")
async def delete_user_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """删除 Agent（同时删除 AGENT.md 文件和 MySQL 记录）"""
    record = await UserAgentDao.get_by_id(agent_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agent不存在")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除该Agent")

    # 删除 AGENT.md 文件及目录
    agent_dir = _get_agent_dir(record.user_id, record.name)
    if agent_dir.exists():
        import shutil
        shutil.rmtree(agent_dir, ignore_errors=True)
        logger.info(f"删除 Agent 目录: {agent_dir}")

    # 删除 MySQL 记录
    await UserAgentDao.delete_agent(agent_id)

    return {"message": "删除成功"}


@router.get("/tools/list", response_model=ToolListResponse, summary="获取可用工具列表")
async def list_available_tools(
    current_user: User = Depends(get_current_user),
):
    """获取所有可用工具列表（供前端选择工具时使用）"""
    tools = []
    for name, tool in AgentToolsWithName.items():
        description = ""
        if hasattr(tool, "description") and tool.description:
            description = tool.description[:200]
        tools.append(ToolInfo(name=name, description=description))
    return ToolListResponse(tools=tools)


# ========== 辅助函数 ==========

def _read_tools_from_md(agent_path: str) -> list:
    """从 AGENT.md 读取工具列表"""
    config = _read_full_agent_md(agent_path)
    return config.get("tools", [])


def _read_full_agent_md(agent_path: str) -> dict:
    """从 AGENT.md 读取完整配置"""
    from app.core.agents.custom.loader import load_agent_config

    config = load_agent_config(agent_path)
    if config:
        return {
            "name": config.name,
            "display_name": config.display_name,
            "description": config.description,
            "tools": config.tools,
            "system_prompt": config.system_prompt,
        }
    return {"tools": [], "system_prompt": ""}
