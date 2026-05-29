"""工作区文件API - 管理和下载 Agent 生成的文件"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from loguru import logger

from app.api.dependencies import get_current_user, get_current_user_optional
from app.config import settings
from app.utils.format import fmt_size
from app.database.models.user import User
from app.auth.auth_jwt import JWTAuth
from app.auth.config import AuthConfig

router = APIRouter(prefix="/workspace", tags=["工作区文件"])


# MIME 类型映射
MIME_MAP = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".html": "text/html",
    ".csv": "text/csv",
    ".json": "application/json",
    ".xml": "application/xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".py": "text/x-python",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".zip": "application/zip",
}

# 图片扩展名（浏览器内嵌显示）
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}


@router.get("/list", summary="列出工作区文件（分页）")
async def list_workspace_files(
    path: str = "",
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
):
    """列出工作区指定目录下的文件，支持分页"""
    workspace = settings.file_workspace_path(current_user.id)
    target = workspace / path if path else workspace

    # 安全检查
    try:
        target.resolve().relative_to(workspace.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    if not target.exists():
        return {"items": [], "path": path, "total": 0, "page": page, "page_size": page_size, "total_pages": 0}

    # 收集所有条目
    all_items = []
    for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), str(p).lower())):
        rel = item.relative_to(workspace)
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


@router.get("/download/{file_path:path}", summary="下载工作区文件")
async def download_workspace_file(
    file_path: str,
    token: str = "",
    current_user: User | None = Depends(get_current_user_optional),
):
    """下载工作区文件（支持 Header 或 URL token 认证）"""
    # 认证：Header 认证 或 URL token 认证
    user = current_user
    if not user and token:
        try:
            config = AuthConfig()
            jwt_auth = JWTAuth(config)
            payload = jwt_auth.verify_token(token, required_type="access")
            from app.database.dao.user_dao import UserDAO
            from app.database.session import get_async_session
            # 同步获取 session
            async for session in get_async_session():
                user_id = int(payload.get("sub"))
                from app.database.dao.user_dao import UserDAO
                user = await UserDAO.get_user_by_id(session, user_id)
                break
        except Exception:
            pass

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="认证失败，请先登录")

    workspace = settings.file_workspace_path(user.id)
    full_path = workspace / file_path

    # 安全检查：防止路径穿越
    try:
        full_path.resolve().relative_to(workspace.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    if full_path.is_dir():
        raise HTTPException(status_code=400, detail="路径是目录，不是文件")

    # 获取 MIME 类型
    ext = full_path.suffix.lower()
    media_type = MIME_MAP.get(ext, "application/octet-stream")

    # 图片格式使用 inline 方式（浏览器内嵌显示）
    is_image = ext in IMAGE_EXTENSIONS
    content_disposition_type = "inline" if is_image else "attachment"

    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type=media_type,
        content_disposition_type=content_disposition_type,
    )


@router.get("/info/{file_path:path}", summary="获取工作区文件信息")
async def get_workspace_file_info(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """获取工作区文件信息"""
    workspace = settings.file_workspace_path(current_user.id)
    full_path = workspace / file_path

    # 安全检查
    try:
        full_path.resolve().relative_to(workspace.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    if full_path.is_dir():
        return {
            "name": full_path.name,
            "path": file_path,
            "type": "directory",
        }

    stat = full_path.stat()
    from datetime import datetime
    ext = full_path.suffix.lower()
    return {
        "name": full_path.name,
        "path": file_path,
        "type": "file",
        "size": stat.st_size,
        "size_text": fmt_size(stat.st_size),
        "format": ext.lstrip("."),
        "modify_time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
    }


@router.delete("/delete/{file_path:path}", summary="删除工作区文件或目录")
async def delete_workspace_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """删除工作区中的文件或目录"""
    workspace = settings.file_workspace_path(current_user.id)
    full_path = workspace / file_path

    # 安全检查：防止路径穿越
    try:
        full_path.resolve().relative_to(workspace.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法路径")

    # 禁止删除工作区根目录
    if full_path.resolve() == workspace.resolve():
        raise HTTPException(status_code=400, detail="不能删除工作区根目录")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件或目录不存在")

    try:
        if full_path.is_dir():
            shutil.rmtree(full_path)
            logger.info(f"删除目录: {file_path}")
        else:
            full_path.unlink()
            logger.info(f"删除文件: {file_path}")
        return {"message": "删除成功", "path": file_path}
    except Exception as e:
        logger.error(f"删除失败: {file_path}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
