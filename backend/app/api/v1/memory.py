"""长期记忆管理API"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.services.memory_service import get_memory_service
from app.schemas.memory import (
    MemoryResponse,
    MemoryListResponse,
    MemoryCreateRequest,
    MemoryUpdateRequest
)

router = APIRouter(prefix="/memory", tags=["长期记忆"])


@router.get("/", response_model=MemoryListResponse, summary="获取用户记忆列表")
async def list_memories(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有长期记忆"""
    memory_service = get_memory_service()
    results = await memory_service.list_memories(user_id=current_user.id, limit=200)

    items = [
        MemoryResponse(
            memory_id=m.get("memory_id", ""),
            content=m.get("content", ""),
            memory_type=m.get("memory_type", "fact"),
            source_dialog_id=m.get("source_dialog_id", ""),
            created_at=m.get("created_at")
        )
        for m in results
    ]

    return MemoryListResponse(total=len(items), items=items)


@router.post("/", response_model=MemoryResponse, summary="手动添加记忆")
async def create_memory(
    data: MemoryCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """手动添加一条长期记忆"""
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="记忆内容不能为空")

    if data.memory_type not in ("preference", "fact", "insight"):
        raise HTTPException(status_code=400, detail="记忆类型必须是 preference/fact/insight")

    memory_service = get_memory_service()
    memory_id = await memory_service.add_memory_manual(
        user_id=current_user.id,
        content=data.content.strip(),
        memory_type=data.memory_type
    )

    if not memory_id:
        raise HTTPException(status_code=500, detail="添加记忆失败")

    return MemoryResponse(
        memory_id=memory_id,
        content=data.content.strip(),
        memory_type=data.memory_type,
        source_dialog_id="manual",
        created_at=None
    )


@router.put("/{memory_id}", response_model=MemoryResponse, summary="更新记忆")
async def update_memory(
    memory_id: str,
    data: MemoryUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """更新一条长期记忆"""
    if data.memory_type and data.memory_type not in ("preference", "fact", "insight"):
        raise HTTPException(status_code=400, detail="记忆类型必须是 preference/fact/insight")

    memory_service = get_memory_service()
    success = await memory_service.update_memory(
        memory_id=memory_id,
        content=data.content,
        memory_type=data.memory_type
    )

    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在或更新失败")

    # 查询更新后的记录
    results = await memory_service.list_memories(user_id=current_user.id, limit=200)
    updated = next((m for m in results if m.get("memory_id") == memory_id), None)

    if not updated:
        raise HTTPException(status_code=404, detail="更新后未找到记忆")

    return MemoryResponse(
        memory_id=updated.get("memory_id", ""),
        content=updated.get("content", ""),
        memory_type=updated.get("memory_type", "fact"),
        source_dialog_id=updated.get("source_dialog_id", ""),
        created_at=updated.get("created_at")
    )


@router.delete("/{memory_id}", summary="删除记忆")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除一条长期记忆"""
    memory_service = get_memory_service()
    success = await memory_service.delete_memory(memory_id)

    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在或删除失败")

    return {"message": "删除成功"}
