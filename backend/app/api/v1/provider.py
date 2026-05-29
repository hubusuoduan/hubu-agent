"""LLM Provider 管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.database.dao.llm_provider_dao import LLMProviderDao
from app.database.models.llm_provider import LLMProviderTable
from app.schemas.llm_provider import (
    CreateProviderRequest,
    UpdateProviderRequest,
    ProviderResponse,
    ProviderBriefResponse,
    ProviderDetailResponse,
)

router = APIRouter()


@router.get("/list", summary="获取当前用户的所有Provider")
async def list_providers(current_user: User = Depends(get_current_user)):
    """获取当前用户的所有Provider列表（隐藏api_key）"""
    providers = await LLMProviderDao.list_by_user(current_user.id)
    return {
        "providers": [
            ProviderBriefResponse(
                id=p.id,
                model=p.model,
                enable=p.enable
            )
            for p in providers
        ]
    }


@router.get("/enabled", summary="获取当前用户启用的Provider")
async def get_enabled_provider(current_user: User = Depends(get_current_user)):
    """获取当前用户启用的Provider信息（隐藏api_key）"""
    provider = await LLMProviderDao.get_enabled(current_user.id)
    if not provider:
        return {"provider": None}
    return {
        "provider": ProviderBriefResponse(
            id=provider.id,
            model=provider.model,
            enable=provider.enable
        )
    }


@router.get("/{provider_id}/detail", summary="获取Provider详情（编辑用）")
async def get_provider_detail(
    provider_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取Provider详情，api_key脱敏，base_url完整返回，用于编辑表单回填"""
    provider = await LLMProviderDao.get_by_id_and_user(provider_id, current_user.id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider不存在")

    # 脱敏 api_key：保留前3位和后4位，中间用****替代
    raw_key = provider.api_key or ""
    if len(raw_key) > 7:
        masked_key = raw_key[:3] + "****" + raw_key[-4:]
    elif len(raw_key) > 0:
        masked_key = raw_key[:1] + "****"
    else:
        masked_key = ""

    return ProviderDetailResponse(
        id=provider.id,
        api_key=masked_key,
        base_url=provider.base_url,
        model=provider.model,
        enable=provider.enable,
    )


@router.post("", summary="创建Provider")
async def create_provider(
    request: CreateProviderRequest,
    current_user: User = Depends(get_current_user)
):
    """创建新的LLM Provider"""
    provider = LLMProviderTable(
        user_id=current_user.id,
        api_key=request.api_key,
        base_url=request.base_url,
        model=request.model,
        enable=request.enable
    )
    created = await LLMProviderDao.create(provider)
    return {
        "success": True,
        "provider": ProviderBriefResponse(
            id=created.id,
            model=created.model,
            enable=created.enable
        )
    }


@router.put("/{provider_id}", summary="更新Provider")
async def update_provider(
    provider_id: int,
    request: UpdateProviderRequest,
    current_user: User = Depends(get_current_user)
):
    """更新Provider配置"""
    # 只更新非None的字段
    kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    updated = await LLMProviderDao.update(provider_id, current_user.id, **kwargs)
    if not updated:
        raise HTTPException(status_code=404, detail="Provider不存在")

    return {
        "success": True,
        "provider": ProviderBriefResponse(
            id=updated.id,
            model=updated.model,
            enable=updated.enable
        )
    }


@router.delete("/{provider_id}", summary="删除Provider")
async def delete_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除Provider"""
    deleted = await LLMProviderDao.delete(provider_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider不存在")
    return {"success": True}


@router.post("/{provider_id}/enable", summary="启用Provider")
async def enable_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user)
):
    """启用指定的Provider（互斥，自动关闭其他）"""
    provider = await LLMProviderDao.enable_provider(provider_id, current_user.id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider不存在")
    return {
        "success": True,
        "provider": ProviderBriefResponse(
            id=provider.id,
            model=provider.model,
            enable=provider.enable
        )
    }
