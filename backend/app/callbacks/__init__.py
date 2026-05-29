"""Callbacks 模块"""
from contextvars import ContextVar
from app.callbacks.usage_metadata_callback import (
    UsageMetadataCallback,
    usage_metadata_callback,
)

# 当前请求的工作区目录路径
current_workspace_dir: ContextVar[str] = ContextVar("current_workspace_dir", default="")
# 当前请求的 Skills 目录路径（多个路径用 os.pathsep 分隔）
current_skills_dir: ContextVar[str] = ContextVar("current_skills_dir", default="")

__all__ = [
    "UsageMetadataCallback",
    "usage_metadata_callback",
    "current_workspace_dir",
    "current_skills_dir",
]
