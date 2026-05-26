"""对话管理API"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from loguru import logger

from app.database.dao.dialog_dao import DialogDao
from app.database.dao.history_dao import HistoryDao
from app.database.session import get_async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.schemas.dialog import (
    CreateDialogRequest,
    UpdateDialogNameRequest,
    UpdateDialogPinRequest,
    UpdateDialogStarRequest,
)

router = APIRouter()


@router.post("/create", summary="创建新对话")
async def create_dialog(
    request: CreateDialogRequest = CreateDialogRequest(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    创建新对话

    - **name**: 对话名称（默认"新对话"）

    返回创建的对话信息
    """
    try:
        dialog = await DialogDao.create_dialog(
            name=request.name,
            user_id=current_user.id
        )
        return {
            "dialog_id": dialog.dialog_id,
            "name": dialog.name,
            "user_id": dialog.user_id,
            "create_time": dialog.create_time.isoformat() if dialog.create_time else None,
            "update_time": dialog.update_time.isoformat() if dialog.update_time else None
        }
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")


@router.get("/list", summary="获取对话列表")
async def get_dialog_list(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取当前用户的对话列表

    - **limit**: 限制返回数量（默认50）

    返回对话列表，按更新时间倒序
    """
    try:
        dialogs = await DialogDao.get_dialogs_by_user_id(
            user_id=current_user.id,
            limit=limit
        )
        return {
            "dialogs": [
                {
                    "dialog_id": d.dialog_id,
                    "name": d.name,
                    "create_time": d.create_time.isoformat() if d.create_time else None,
                    "update_time": d.update_time.isoformat() if d.update_time else None,
                    "is_pinned": bool(d.is_pinned),
                    "is_starred": bool(d.is_starred),
                    "pinned_at": d.pinned_at.isoformat() if d.pinned_at else None
                }
                for d in dialogs
            ],
            "total": len(dialogs)
        }
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@router.get("/{dialog_id}", summary="获取对话详情")
async def get_dialog(
    dialog_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    根据ID获取对话详情

    - **dialog_id**: 对话ID
    """
    try:
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        # 权限校验：只能查看自己的对话
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问该对话")
        return {
            "dialog_id": dialog.dialog_id,
            "name": dialog.name,
            "user_id": dialog.user_id,
            "summary": dialog.summary,
            "create_time": dialog.create_time.isoformat() if dialog.create_time else None,
            "update_time": dialog.update_time.isoformat() if dialog.update_time else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话详情失败: {str(e)}")


@router.put("/{dialog_id}/name", summary="更新对话名称")
async def update_dialog_name(
    dialog_id: str,
    request: UpdateDialogNameRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    更新对话名称

    - **dialog_id**: 对话ID
    - **name**: 新名称
    """
    try:
        # 权限校验
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改该对话")

        updated = await DialogDao.update_dialog_name(dialog_id, request.name)
        if not updated:
            raise HTTPException(status_code=404, detail="对话不存在")
        return {
            "dialog_id": updated.dialog_id,
            "name": updated.name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话名称失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新对话名称失败: {str(e)}")


@router.delete("/{dialog_id}", summary="删除对话")
async def delete_dialog(
    dialog_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    删除对话（同时删除关联的历史记录）

    - **dialog_id**: 对话ID
    """
    try:
        # 权限校验
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除该对话")

        success = await DialogDao.delete_dialog(dialog_id)
        if not success:
            raise HTTPException(status_code=404, detail="对话不存在")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")


@router.delete("/{dialog_id}/messages", summary="批量删除对话消息")
async def batch_delete_messages(
    dialog_id: str,
    message_ids: List[str] = Query(..., description="要删除的消息ID列表"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    批量删除对话中的指定消息

    - **dialog_id**: 对话ID
    - **message_ids**: 要删除的消息ID列表（query参数，多个值）
    """
    try:
        # 权限校验
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权操作该对话")

        deleted_count = await HistoryDao.delete_messages_by_ids(dialog_id, message_ids)
        return {
            "dialog_id": dialog_id,
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量删除消息失败: {str(e)}")


@router.put("/{dialog_id}/pin", summary="更新对话置顶状态")
async def update_dialog_pin(
    dialog_id: str,
    request: UpdateDialogPinRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权操作该对话")

        updated = await DialogDao.update_dialog_pin(dialog_id, request.is_pinned)
        if not updated:
            raise HTTPException(status_code=404, detail="对话不存在")
        return {
            "dialog_id": updated.dialog_id,
            "is_pinned": bool(updated.is_pinned),
            "pinned_at": updated.pinned_at.isoformat() if updated.pinned_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话置顶状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新对话置顶状态失败: {str(e)}")


@router.put("/{dialog_id}/star", summary="更新对话收藏状态")
async def update_dialog_star(
    dialog_id: str,
    request: UpdateDialogStarRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权操作该对话")

        updated = await DialogDao.update_dialog_star(dialog_id, request.is_starred)
        if not updated:
            raise HTTPException(status_code=404, detail="对话不存在")
        return {
            "dialog_id": updated.dialog_id,
            "is_starred": bool(updated.is_starred)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话收藏状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新对话收藏状态失败: {str(e)}")


@router.get("/{dialog_id}/history", summary="获取对话历史")
async def get_dialog_history(
    dialog_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取对话的历史消息

    - **dialog_id**: 对话ID
    - **limit**: 限制返回数量（默认50）
    """
    try:
        # 权限校验
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问该对话")

        histories = await HistoryDao.get_history_by_dialog_id(
            dialog_id=dialog_id,
            limit=limit
        )
        messages = [
            {
                "id": h.id,
                "role": h.role,
                "content": h.content,
                "create_time": h.create_time.isoformat() if h.create_time else None
            }
            for h in histories
        ]
        return {
            "dialog_id": dialog_id,
            "messages": messages,
            "total": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")
