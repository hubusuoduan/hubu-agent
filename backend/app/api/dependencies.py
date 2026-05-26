"""认证依赖函数"""
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from app.database.session import get_async_session
from app.auth.auth_jwt import JWTAuth
from app.auth.config import AuthConfig
from app.auth.exceptions import InvalidTokenError
from app.database.dao.user_dao import UserDAO
from app.database.models.user import User

# HTTP Bearer 认证方案
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """
    获取当前登录用户
    
    Args:
        request: HTTP 请求
        credentials: HTTP 认证凭证
        session: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出
    """
    try:
        # 验证 Token
        config = AuthConfig()
        jwt_auth = JWTAuth(config)
        
        token = credentials.credentials
        payload = jwt_auth.verify_token(token, required_type="access")
        
        # 获取用户 ID
        user_id = int(payload.get("sub"))
        
        # 查询用户
        user = await UserDAO.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        
        # 检查用户是否激活
        if not user.is_active:
            raise HTTPException(status_code=403, detail="用户已被禁用")
        
        return user
        
    except HTTPException:
        raise
    except InvalidTokenError as e:
        # Token无效或过期，给出明确提示
        logger.warning(f"Token验证失败: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token已过期或无效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"认证异常: {e}")
        raise HTTPException(status_code=401, detail=f"认证失败: {str(e)}")


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    session: AsyncSession = Depends(get_async_session)
) -> User | None:
    """
    可选的用户认证（不强制要求登录）
    
    Args:
        request: HTTP 请求
        credentials: HTTP 认证凭证（可选）
        session: 数据库会话
        
    Returns:
        当前用户对象或 None
    """
    if not credentials:
        return None
    
    try:
        config = AuthConfig()
        jwt_auth = JWTAuth(config)
        
        token = credentials.credentials
        payload = jwt_auth.verify_token(token, required_type="access")
        
        user_id = int(payload.get("sub"))
        user = await UserDAO.get_user_by_id(session, user_id)
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None
