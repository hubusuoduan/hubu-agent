
"""对话导出API"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from loguru import logger

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.schemas.export import ExportDialogRequest
from app.services.export_service import ExportService

router = APIRouter()


@router.post("/{dialog_id}/export", summary="导出对话")
async def export_dialog(
    dialog_id: str,
    request: ExportDialogRequest = ExportDialogRequest(),
    current_user: User = Depends(get_current_user),
):
    """
    导出对话为指定格式

    - **dialog_id**: 对话ID
    - **format**: 导出格式（markdown）
    - **range**: 导出范围（all/recent/custom）
    - **recent_count**: 当range=recent时，指定最近的消息条数
    - **start_index**: 当range=custom时，起始消息索引
    - **end_index**: 当range=custom时，结束消息索引
    """
    try:
        file_bytes, filename, content_type = await ExportService.export_dialog(
            dialog_id=dialog_id,
            request=request,
            user_id=current_user.id
        )

        # 设置Content-Disposition（中文文件名需要URL编码）
        from urllib.parse import quote
        encoded_filename = quote(filename)
        disposition = f"attachment; filename=\"{encoded_filename}\"; filename*=UTF-8''{encoded_filename}"

        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": disposition,
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"导出对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出对话失败: {str(e)}")
