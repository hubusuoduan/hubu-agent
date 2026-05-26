"""模型管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.services.llm_service import LLMService

router = APIRouter()


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    model: str
    is_default: bool = False
    is_current: bool = False


class SwitchModelRequest(BaseModel):
    """切换模型请求"""
    provider_id: str


@router.get("/current", summary="获取当前模型")
async def get_current_model(current_user: User = Depends(get_current_user)):
    """获取当前使用的模型信息"""
    provider = LLMService.get_current_provider()
    return {
        "id": provider.get("id", "default"),
        "name": provider.get("name", "未知"),
        "model": provider.get("model", "unknown"),
        "is_default": provider.get("is_default", False)
    }


@router.get("/list", summary="获取所有模型列表")
async def list_models(current_user: User = Depends(get_current_user)):
    """获取所有可用的模型列表"""
    providers = LLMService.get_all_providers()
    return {
        "models": providers,
        "current": LLMService._current_provider_id
    }


@router.post("/switch", summary="切换模型")
async def switch_model(
    request: SwitchModelRequest,
    current_user: User = Depends(get_current_user)
):
    """切换当前使用的模型"""
    try:
        provider = LLMService.switch_provider(request.provider_id)
        return {
            "success": True,
            "current": {
                "id": provider.get("id"),
                "name": provider.get("name"),
                "model": provider.get("model")
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
