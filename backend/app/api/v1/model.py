"""模型管理 API - 兼容旧接口，数据从数据库读取"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/current", summary="获取当前启用的模型")
async def get_current_model(current_user: User = Depends(get_current_user)):
    """获取当前用户启用的模型信息"""
    provider = await LLMService.get_current_provider(current_user.id)
    return {
        "id": provider.get("id"),
        "model": provider.get("model", "未配置"),
        "enable": provider.get("enable", False)
    }


@router.get("/list", summary="获取用户所有模型列表")
async def list_models(current_user: User = Depends(get_current_user)):
    """获取当前用户的所有模型列表"""
    providers = await LLMService.get_all_providers(current_user.id)
    return {"models": providers}
