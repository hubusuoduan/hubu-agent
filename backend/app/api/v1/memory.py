"""长期记忆管理API"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.database.session import get_async_session
from sqlmodel.ext.asyncio.session import AsyncSession
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
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    memory_type: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取长期记忆列表（支持分页和搜索）

    所有用户只能查看自己的记忆。

    Args:
        page: 页码，从1开始
        page_size: 每页数量
        keyword: 搜索关键词
        memory_type: 按类型筛选（preference/fact/insight）
        user_id: 保留参数（暂未使用）
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    offset = (page - 1) * page_size

    # 所有用户只能查看自己的记忆
    query_user_id = current_user.id

    memory_service = get_memory_service()
    result = await memory_service.list_memories(
        user_id=query_user_id,
        limit=page_size,
        offset=offset,
        keyword=keyword or "",
        memory_type=memory_type or ""
    )

    items = []
    for m in result.get("items", []):
        items.append(MemoryResponse(
            memory_id=m.get("memory_id", ""),
            user_id=m.get("user_id"),
            content=m.get("content", ""),
            memory_type=m.get("memory_type", "fact"),
            source_dialog_id=m.get("source_dialog_id", ""),
            created_at=m.get("created_at"),
            importance=m.get("importance", 3)
        ))

    return MemoryListResponse(total=result.get("total", 0), items=items)


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
        memory_type=data.memory_type,
        importance=data.importance
    )

    if not memory_id:
        raise HTTPException(status_code=500, detail="添加记忆失败")

    return MemoryResponse(
        memory_id=memory_id,
        content=data.content.strip(),
        memory_type=data.memory_type,
        source_dialog_id="manual",
        created_at=None,
        importance=data.importance
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

    # 校验记忆归属
    result = await memory_service.list_memories(user_id=current_user.id, limit=200, offset=0)
    owned_ids = {m.get("memory_id") for m in result.get("items", [])}
    if memory_id not in owned_ids:
        raise HTTPException(status_code=403, detail="无权操作该记忆")

    success = await memory_service.update_memory(
        memory_id=memory_id,
        content=data.content,
        memory_type=data.memory_type,
        importance=data.importance
    )

    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在或更新失败")

    # 查询更新后的记录
    result = await memory_service.list_memories(user_id=current_user.id, limit=200, offset=0)
    updated = next((m for m in result.get("items", []) if m.get("memory_id") == memory_id), None)

    if not updated:
        raise HTTPException(status_code=404, detail="更新后未找到记忆")

    return MemoryResponse(
        memory_id=updated.get("memory_id", ""),
        user_id=updated.get("user_id"),
        content=updated.get("content", ""),
        memory_type=updated.get("memory_type", "fact"),
        source_dialog_id=updated.get("source_dialog_id", ""),
        created_at=updated.get("created_at"),
        importance=updated.get("importance", 3)
    )


@router.delete("/{memory_id}", summary="删除记忆")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除一条长期记忆"""
    memory_service = get_memory_service()

    # 校验记忆归属
    result = await memory_service.list_memories(user_id=current_user.id, limit=200, offset=0)
    owned_ids = {m.get("memory_id") for m in result.get("items", [])}
    if memory_id not in owned_ids:
        raise HTTPException(status_code=403, detail="无权操作该记忆")

    success = await memory_service.delete_memory(memory_id)

    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在或删除失败")

    return {"message": "删除成功"}
