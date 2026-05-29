"""系统配置 API - 允许前端查看和修改用户级运行时配置

所有配置存储在 user_settings 表（一条 JSON 记录），默认值来自 CONFIGURABLE_FIELDS
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.services.settings_service import SettingsService, SettingsFactory, CONFIGURABLE_FIELDS

router = APIRouter()


async def ensure_settings_loaded(current_user: User = Depends(get_current_user)) -> User:
    """确保用户配置已加载到 SettingsFactory 缓存"""
    if current_user.id not in SettingsFactory._user_settings:
        await SettingsFactory.create_for_user()
    return current_user


class SetSettingRequest(BaseModel):
    """单个配置更新请求"""
    value: Any


class BatchSetSettingRequest(BaseModel):
    """批量配置更新请求"""
    settings: Dict[str, Any]


@router.get("", summary="获取所有可配置项（按分组）")
async def get_settings(current_user: User = Depends(ensure_settings_loaded)):
    """获取所有可配置项，按分组组织，含当前值、默认值和元信息"""
    try:
        grouped = await SettingsService.get_user_settings_grouped(current_user.id)
        return {"settings": grouped}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")


@router.get("/flat", summary="获取所有可配置项（平铺列表）")
async def get_settings_flat(current_user: User = Depends(ensure_settings_loaded)):
    """获取所有可配置项的平铺列表"""
    try:
        all_settings = await SettingsService.get_user_all_settings(current_user.id)
        return {"settings": all_settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")


@router.get("/{key}", summary="获取单个配置项")
async def get_setting(
    key: str,
    current_user: User = Depends(ensure_settings_loaded)
):
    """获取单个配置项的详细信息"""
    if key not in CONFIGURABLE_FIELDS:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在或不允许访问")

    try:
        meta = CONFIGURABLE_FIELDS[key]
        default_value = meta["default"]
        current_value = SettingsFactory.get(current_user.id, key)

        return {
            "key": key,
            "type": meta["type"],
            "group": meta["group"],
            "desc": meta["desc"],
            "default_value": default_value,
            "current_value": current_value,
            "is_modified": current_value != default_value,
            "min": meta.get("min"),
            "max": meta.get("max"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")


@router.put("/{key}", summary="更新单个配置项")
async def update_setting(
    key: str,
    request: SetSettingRequest,
    current_user: User = Depends(ensure_settings_loaded)
):
    """更新单个配置项的值"""
    try:
        result = await SettingsService.set_user_value(current_user.id, key, request.value)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", summary="批量更新配置项")
async def batch_update_settings(
    request: BatchSetSettingRequest,
    current_user: User = Depends(ensure_settings_loaded)
):
    """批量更新配置项"""
    results = []
    errors = []

    for key, value in request.settings.items():
        try:
            result = await SettingsService.set_user_value(current_user.id, key, value)
            results.append(result)
        except (ValueError, RuntimeError) as e:
            errors.append({"key": key, "error": str(e)})

    return {
        "success": len(errors) == 0,
        "updated": results,
        "errors": errors if errors else None
    }


@router.delete("/{key}", summary="重置单个配置项")
async def reset_setting(
    key: str,
    current_user: User = Depends(ensure_settings_loaded)
):
    """重置单个配置项为默认值"""
    try:
        await SettingsService.reset_user_value(current_user.id, key)
        return {"success": True, "key": key}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset", summary="重置所有配置项")
async def reset_all_settings(current_user: User = Depends(ensure_settings_loaded)):
    """重置所有配置项为默认值"""
    try:
        count = await SettingsService.reset_user_all(current_user.id)
        return {"success": True, "reset_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置配置失败: {e}")
