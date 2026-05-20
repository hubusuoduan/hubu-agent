"""认证服务层"""
from datetime import datetime
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger
from passlib.context import CryptContext

from app.database.models.user import User
from app.database.dao.user_dao import UserDAO
from app.auth.auth_jwt import JWTAuth
from app.auth.config import AuthConfig
from app.auth.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    InvalidTokenError
)
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserInfo

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.config = AuthConfig()
        self.jwt_auth = JWTAuth(self.config)
    
    def _hash_password(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            密码是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    async def register_user(self, user_data: UserRegister) -> UserInfo:
        """
        用户注册
        
        Args:
            user_data: 注册信息
            
        Returns:
            用户信息
            
        Raises:
            UserAlreadyExistsError: 用户已存在
        """
        # 检查用户是否已存在
        existing_user = await UserDAO.get_user_by_username(self.session, user_data.username)
        if existing_user:
            raise UserAlreadyExistsError(f"用户名 {user_data.username} 已存在")
        
        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = await UserDAO.get_user_by_email(self.session, user_data.email)
            if existing_email:
                raise UserAlreadyExistsError(f"邮箱 {user_data.email} 已被注册")
        
        # 创建新用户
        new_user = User(
            username=user_data.username,
            password_hash=self._hash_password(user_data.password),
            email=user_data.email,
            nickname=user_data.nickname
        )
        
        created_user = await UserDAO.create_user(self.session, new_user)
        logger.info(f"用户注册成功: {created_user.username}")
        
        return UserInfo(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            nickname=created_user.nickname,
            avatar=created_user.avatar,
            is_active=created_user.is_active
        )
    
    async def login(self, login_data: UserLogin) -> TokenResponse:
        """
        用户登录
        
        Args:
            login_data: 登录信息
            
        Returns:
            Token响应
            
        Raises:
            InvalidCredentialsError: 凭证无效
        """
        # 查找用户
        user = await UserDAO.get_user_by_username(self.session, login_data.username)
        if not user:
            raise InvalidCredentialsError("用户名或密码错误")
        
        # 验证密码
        if not self._verify_password(login_data.password, user.password_hash):
            raise InvalidCredentialsError("用户名或密码错误")
        
        # 检查用户是否激活
        if not user.is_active:
            raise InvalidCredentialsError("用户已被禁用")
        
        # 生成Token
        access_token = self.jwt_auth.create_access_token(
            subject=user.id,
            user_claims={"username": user.username}
        )
        refresh_token = self.jwt_auth.create_refresh_token(
            subject=user.id,
            user_claims={"username": user.username}
        )
        
        logger.info(f"用户登录成功: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer"
        )
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        刷新访问Token
        
        Args:
            refresh_token: 刷新Token
            
        Returns:
            新的Token响应
            
        Raises:
            InvalidTokenError: Token无效
        """
        # 验证刷新Token
        try:
            payload = self.jwt_auth.verify_token(refresh_token, required_type="refresh")
            user_id = int(payload.get("sub"))
        except Exception as e:
            raise InvalidTokenError(f"刷新Token无效: {str(e)}")
        
        # 查找用户
        user = await UserDAO.get_user_by_id(self.session, user_id)
        if not user or not user.is_active:
            raise InvalidTokenError("用户不存在或已被禁用")
        
        # 生成新的Token
        access_token = self.jwt_auth.create_access_token(
            subject=user.id,
            user_claims={"username": user.username}
        )
        new_refresh_token = self.jwt_auth.create_refresh_token(
            subject=user.id,
            user_claims={"username": user.username}
        )
        
        logger.info(f"Token刷新成功: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer"
        )
    
    async def get_current_user(self, access_token: str) -> UserInfo:
        """
        获取当前用户信息
        
        Args:
            access_token: 访问Token
            
        Returns:
            用户信息
        """
        # 验证Token
        payload = self.jwt_auth.verify_token(access_token, required_type="access")
        user_id = int(payload.get("sub"))
        
        # 查找用户
        user = await UserDAO.get_user_by_id(self.session, user_id)
        if not user:
            raise InvalidTokenError("用户不存在")
        
        return UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            avatar=user.avatar,
            is_active=user.is_active
        )
