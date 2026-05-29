"""Embedding Provider 管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.database.dao.embedding_provider_dao import EmbeddingProviderDao
from app.database.models.embedding_provider import EmbeddingProviderTable
from app.schemas.embedding_provider import (
    CreateEmbeddingProviderRequest,
    UpdateEmbeddingProviderRequest,
    EmbeddingProviderResponse,
    EmbeddingProviderDetailResponse,
)

router = APIRouter()


def mask_api_key(raw_key: str) -> str:
    """脱敏 api_key：保留前3位和后4位，中间用****替代"""
    if len(raw_key) > 7:
        return raw_key[:3] + "****" + raw_key[-4:]
    elif len(raw_key) > 0:
        return raw_key[:1] + "****"
    return ""


@router.get("", summary="获取当前用户的Embedding Provider")
async def get_embedding_provider(current_user: User = Depends(get_current_user)):
    """获取用户的Embedding Provider配置（隐藏api_key）"""
    provider = await EmbeddingProviderDao.get_by_user(current_user.id)
    if not provider:
        return {"provider": None}
    return {
        "provider": EmbeddingProviderResponse(
            id=provider.id,
            model=provider.model,
        )
    }


@router.get("/detail", summary="获取Embedding Provider详情（编辑用）")
async def get_embedding_provider_detail(current_user: User = Depends(get_current_user)):
    """获取Embedding Provider详情，api_key脱敏，base_url完整返回"""
    provider = await EmbeddingProviderDao.get_by_user(current_user.id)
    if not provider:
        return {"provider": None}

    return {
        "provider": EmbeddingProviderDetailResponse(
            id=provider.id,
            api_key=mask_api_key(provider.api_key),
            base_url=provider.base_url,
            model=provider.model,
        )
    }


@router.post("", summary="创建或更新Embedding Provider")
async def create_embedding_provider(
    request: CreateEmbeddingProviderRequest,
    current_user: User = Depends(get_current_user)
):
    """创建Embedding Provider（每用户仅一条，已存在则更新）"""
    provider = EmbeddingProviderTable(
        user_id=current_user.id,
        api_key=request.api_key,
        base_url=request.base_url,
        model=request.model,
    )
    created = await EmbeddingProviderDao.create(provider)
    return {
        "success": True,
        "provider": EmbeddingProviderResponse(
            id=created.id,
            model=created.model,
        )
    }


@router.put("", summary="更新Embedding Provider")
async def update_embedding_provider(
    request: UpdateEmbeddingProviderRequest,
    current_user: User = Depends(get_current_user)
):
    """更新Embedding Provider配置"""
    # 只更新非None的字段
    kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    updated = await EmbeddingProviderDao.update(current_user.id, **kwargs)
    if not updated:
        raise HTTPException(status_code=404, detail="Embedding Provider未配置，请先创建")

    return {
        "success": True,
        "provider": EmbeddingProviderResponse(
            id=updated.id,
            model=updated.model,
        )
    }


@router.delete("", summary="删除Embedding Provider")
async def delete_embedding_provider(current_user: User = Depends(get_current_user)):
    """删除用户的Embedding Provider"""
    deleted = await EmbeddingProviderDao.delete(current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Embedding Provider未配置")
    return {"success": True}
