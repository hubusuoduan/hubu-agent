"""报告文件API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import os

from app.database.session import get_async_session
from app.database.models.report import ReportTable, ReportStatus
from app.api.dependencies import get_current_user, get_current_user_optional
from app.database.models.user import User
from app.auth.auth_jwt import JWTAuth
from app.auth.config import AuthConfig

router = APIRouter(prefix="/report", tags=["报告"])


@router.get("/download/{report_id}", summary="下载报告文件")
async def download_report(
    report_id: str,
    token: str = Query(default=None, description="访问令牌（URL方式下载时使用）"),
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_async_session)
):
    """下载报告文件（支持 Header 或 URL token 认证）"""
    # 认证：Header 认证 或 URL token 认证，至少一种有效
    user = current_user
    if not user and token:
        try:
            config = AuthConfig()
            jwt_auth = JWTAuth(config)
            payload = jwt_auth.verify_token(token, required_type="access")
            from app.database.dao.user_dao import UserDAO
            user_id = int(payload.get("sub"))
            user = await UserDAO.get_user_by_id(session, user_id)
        except Exception:
            pass

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="认证失败，请先登录")

    # 查询报告记录
    report = await session.get(ReportTable, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 检查文件是否存在
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="报告文件不存在或已被删除")

    # 根据格式设置 MIME 类型
    mime_map = {
        "markdown": "text/markdown",
        "txt": "text/plain",
        "html": "text/html",
        "png": "image/png",
        "jpg": "image/jpeg",
        "svg": "image/svg+xml",
    }
    media_type = mime_map.get(report.file_format, "application/octet-stream")

    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type=media_type,
    )


@router.get("/list", summary="获取报告列表")
async def list_reports(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取报告列表（需要认证）"""
    # 获取总数
    total_statement = select(ReportTable)
    total_result = await session.execute(total_statement)
    total = len(total_result.scalars().all())

    # 获取分页数据
    statement = (
        select(ReportTable)
        .order_by(ReportTable.create_time.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    reports = result.scalars().all()

    items = []
    for r in reports:
        items.append({
            "id": r.id,
            "title": r.title,
            "file_name": r.file_name,
            "file_format": r.file_format,
            "file_size": r.file_size,
            "status": r.status,
            "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S") if r.create_time else None,
        })

    return {"total": total, "items": items}


@router.delete("/{report_id}", summary="删除报告")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """删除报告及其文件（需要认证）"""
    report = await session.get(ReportTable, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 删除文件
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except OSError:
            pass

    # 删除数据库记录
    await session.delete(report)
    await session.commit()

    return {"message": "删除成功"}
