"""日志配置模块

基于 loguru 的日志配置，支持：
- 控制台彩色输出（按 LOG_LEVEL 配置，开发调试用）
- 文件按日期分目录输出：
  - logs/2024-01-15/app.log    — WARNING 及以上（业务日志）
  - logs/2024-01-15/error.log  — ERROR 及以上（仅错误，快速定位）
- 第三方库日志过滤：过滤 httpx/httpcore 等噪音
- 按大小滚动 + 按时间保留 + 自动压缩
"""

import sys
from pathlib import Path
from loguru import logger

from app.config import settings, BACKEND_DIR

# 日志文件输出目录（固定为 backend/logs）
LOG_DIR = BACKEND_DIR / "logs"

# 第三方库噪音过滤：这些模块的日志不写入文件
NOISY_MODULES = {
    "httpx",
    "httpcore",
    "urllib3",
    "aiomysql",
    "multipart",
    "uvicorn.access",
}


def _is_noisy_module(record) -> bool:
    """判断日志是否来自噪音模块"""
    return record["name"] in NOISY_MODULES


def _not_noisy(record) -> bool:
    """过滤：排除噪音模块"""
    return not _is_noisy_module(record)


def _date_app_log_path() -> str:
    """生成按日期的 app.log 路径：logs/YYYY-MM-DD/app.log"""
    date_dir = LOG_DIR / "{time:YYYY-MM-DD}"
    return str(date_dir / "app.log")


def _date_error_log_path() -> str:
    """生成按日期的 error.log 路径：logs/YYYY-MM-DD/error.log"""
    date_dir = LOG_DIR / "{time:YYYY-MM-DD}"
    return str(date_dir / "error.log")


def setup_logging():
    """初始化日志配置

    输出策略：
    ┌────────────────────────┬──────────────────┬────────────────┐
    │ 输出目标                │ 级别             │ 说明            │
    ├────────────────────────┼──────────────────┼────────────────┤
    │ 控制台                  │ LOG_LEVEL（INFO） │ 开发调试，全量   │
    │ logs/{date}/app.log    │ WARNING+         │ 业务警告和错误   │
    │ logs/{date}/error.log  │ ERROR+           │ 仅错误，快速定位 │
    └────────────────────────┴──────────────────┴────────────────┘
    """
    # 移除 loguru 默认的 handler
    logger.remove()

    log_level = settings.LOG_LEVEL.upper()

    # 1. 控制台输出：彩色、简洁格式，按 LOG_LEVEL 显示
    logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # 2. 文件输出：按日期分目录，自动创建
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_level = settings.LOG_FILE_LEVEL.upper()

    # 2a. logs/{date}/app.log — 按 LOG_FILE_LEVEL 配置，排除第三方噪音
    logger.add(
        _date_app_log_path(),
        level=file_level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        filter=_not_noisy,
        rotation="10 MB",       # 单文件超过 10MB 滚动
        retention="30 days",    # 保留 30 天
        compression="zip",      # 旧日志压缩
        encoding="utf-8",
        enqueue=True,           # 异步写入
    )

    # 2b. logs/{date}/error.log — 仅 ERROR 及以上，快速定位严重问题
    logger.add(
        _date_error_log_path(),
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        rotation="5 MB",        # 错误文件更小，滚动更快
        retention="90 days",    # 错误日志保留更久
        compression="zip",
        encoding="utf-8",
        enqueue=True,
    )

    logger.info(f"日志配置完成，控制台级别: {log_level}，文件输出: logs/{{日期}}/app.log (WARNING+), error.log (ERROR+)")
