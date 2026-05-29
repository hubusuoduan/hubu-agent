"""认证 API 端点"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.session import get_async_session
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserInfo,
    RefreshTokenRequest,
    UpdateProfile,
    ChangePassword
)


router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)


@router.post("/register", response_model=UserInfo, summary="用户注册")
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_async_session)
):
    """
    用户注册接口
    
    Args:
        user_data: 用户注册信息
        session: 数据库会话
        
    Returns:
        用户信息
    """
    auth_service = AuthService(session)
    try:
        return await auth_service.register_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: UserLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """
    用户登录接口
    
    Args:
        login_data: 用户登录信息
        session: 数据库会话
        
    Returns:
        Token响应
    """
    auth_service = AuthService(session)
    try:
        return await auth_service.login(login_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=TokenResponse, summary="刷新Token")
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    刷新访问Token接口
    
    Args:
        request: 刷新Token请求
        session: 数据库会话
        
    Returns:
        新的Token响应
    """
    auth_service = AuthService(session)
    try:
        return await auth_service.refresh_access_token(request.refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取当前登录用户信息
    
    Args:
        request: HTTP请求
        credentials: HTTP认证凭证
        session: 数据库会话
        
    Returns:
        用户信息
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="缺少认证Token")
    
    auth_service = AuthService(session)
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.put("/profile", response_model=UserInfo, summary="更新个人信息")
async def update_profile(
    profile_data: UpdateProfile,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    更新当前用户个人信息（邮箱、昵称）
    """
    auth_service = AuthService(session)
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        # get_current_user 返回 UserInfo，需要重新查询 ORM 对象
        from app.database.dao.user_dao import UserDAO
        user_obj = await UserDAO.get_user_by_id(session, user.id)
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")
        return await auth_service.update_profile(user_obj, profile_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: ChangePassword,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
):
    """
    修改当前用户密码
    """
    auth_service = AuthService(session)
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        from app.database.dao.user_dao import UserDAO
        user_obj = await UserDAO.get_user_by_id(session, user.id)
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")
        return await auth_service.change_password(user_obj, password_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
