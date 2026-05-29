"""日志文件API - 查看后端日志文件"""
import os
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger

from app.api.dependencies import get_current_user
from app.config import BACKEND_DIR
from app.utils.format import fmt_size
from app.database.models.user import User

router = APIRouter(prefix="/logs", tags=["日志查看"])

# 日志目录（固定为 backend/logs）
LOG_DIR = BACKEND_DIR / "logs"


def _require_admin(user: User):
    """校验管理员权限，非管理员返回403"""
    if user.role != 1:
        raise HTTPException(status_code=403, detail="仅管理员可访问日志")


@router.get("/list", summary="列出日志文件（分页）")
async def list_log_files(
    path: str = "",
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
):
    """列出日志目录下的文件，支持分页（仅管理员）"""
    _require_admin(current_user)
    target = LOG_DIR / path if path else LOG_DIR

    # 安全检查：防止路径穿越
    try:
        target.resolve().relative_to(LOG_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    if not target.exists():
        return {"items": [], "path": path, "total": 0, "page": page, "page_size": page_size, "total_pages": 0}

    # 收集所有条目
    all_items = []
    for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), str(p).lower())):
        rel = item.relative_to(LOG_DIR)
        if item.is_dir():
            all_items.append({
                "name": item.name,
                "path": str(rel),
                "type": "directory",
            })
        else:
            size = item.stat().st_size
            mtime = item.stat().st_mtime
            all_items.append({
                "name": item.name,
                "path": str(rel),
                "type": "file",
                "size": size,
                "size_text": fmt_size(size),
                "format": item.suffix.lstrip("."),
                "modify_time": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
            })

    # 分页
    total = len(all_items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    items = all_items[start:end]

    return {
        "items": items,
        "path": path,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/read/{file_path:path}", summary="读取日志文件内容")
async def read_log_file(
    file_path: str,
    tail: int = Query(500, ge=1, le=5000, description="读取最后N行"),
    current_user: User = Depends(get_current_user),
):
    """读取日志文件内容，默认返回最后500行（仅管理员）"""
    _require_admin(current_user)
    full_path = LOG_DIR / file_path

    # 安全检查：防止路径穿越
    try:
        full_path.resolve().relative_to(LOG_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    if full_path.is_dir():
        raise HTTPException(status_code=400, detail="路径是目录，不是文件")

    # 只允许读取 .log 文件
    if full_path.suffix.lower() != ".log":
        raise HTTPException(status_code=400, detail="只允许读取 .log 文件")

    try:
        # 读取文件最后 N 行
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        tail_lines = lines[-tail:]

        return {
            "path": file_path,
            "name": full_path.name,
            "total_lines": total_lines,
            "showing_lines": len(tail_lines),
            "tail": tail,
            "content": "".join(tail_lines),
        }
    except Exception as e:
        logger.error(f"读取日志文件失败: {file_path}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.delete("/delete/{file_path:path}", summary="删除日志文件")
async def delete_log_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """删除日志文件（不允许删除目录，仅管理员）"""
    _require_admin(current_user)
    full_path = LOG_DIR / file_path

    # 安全检查
    try:
        full_path.resolve().relative_to(LOG_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    # 禁止删除日志根目录
    if full_path.resolve() == LOG_DIR.resolve():
        raise HTTPException(status_code=400, detail="不能删除日志根目录")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    if full_path.is_dir():
        raise HTTPException(status_code=400, detail="不允许删除日志目录")

    try:
        full_path.unlink()
        logger.info(f"删除日志文件: {file_path}")
        return {"message": "删除成功", "path": file_path}
    except Exception as e:
        logger.error(f"删除日志文件失败: {file_path}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
