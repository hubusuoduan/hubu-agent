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
    RefreshTokenRequest
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
