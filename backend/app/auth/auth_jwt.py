"""JWT认证核心逻辑"""
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Union, Sequence
from fastapi import Request

from app.auth.config import AuthConfig
from app.auth.exceptions import (
    InvalidTokenError,
    MissingTokenError,
    AccessTokenRequired,
    RefreshTokenRequired
)


class JWTAuth:
    """JWT认证器"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._token: Optional[str] = None
        self._request: Optional[Request] = None
    
    def _create_token(
        self,
        subject: Union[str, int],
        token_type: str,
        expires_delta: timedelta,
        user_claims: Optional[Dict] = None
    ) -> str:
        """
        创建JWT Token
        
        Args:
            subject: Token主体（通常是用户ID）
            token_type: Token类型（access或refresh）
            expires_delta: 过期时间
            user_claims: 自定义声明
            
        Returns:
            编码后的JWT Token
        """
        encode_data = {
            "sub": str(subject),
            "jti": str(uuid.uuid4()),
            "type": token_type,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + expires_delta
        }
        
        if user_claims:
            encode_data.update(user_claims)
        
        return jwt.encode(
            encode_data,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
    
    def create_access_token(
        self,
        subject: Union[str, int],
        user_claims: Optional[Dict] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问Token
        
        Args:
            subject: Token主体
            user_claims: 自定义声明
            expires_delta: 过期时间（默认使用配置）
            
        Returns:
            访问Token
        """
        if expires_delta is None:
            expires_delta = self.config.access_token_expires
        
        return self._create_token(
            subject=subject,
            token_type="access",
            expires_delta=expires_delta,
            user_claims=user_claims
        )
    
    def create_refresh_token(
        self,
        subject: Union[str, int],
        user_claims: Optional[Dict] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建刷新Token
        
        Args:
            subject: Token主体
            user_claims: 自定义声明
            expires_delta: 过期时间（默认使用配置）
            
        Returns:
            刷新Token
        """
        if expires_delta is None:
            expires_delta = self.config.refresh_token_expires
        
        return self._create_token(
            subject=subject,
            token_type="refresh",
            expires_delta=expires_delta,
            user_claims=user_claims
        )
    
    def _decode_token(self, token: str) -> Dict:
        """
        解码JWT Token
        
        Args:
            token: JWT Token字符串
            
        Returns:
            解码后的Token数据
            
        Raises:
            InvalidTokenError: Token无效或过期
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token已过期")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"无效的Token: {str(e)}")
    
    def verify_token(self, token: str, required_type: str = "access") -> Dict:
        """
        验证Token并返回解码数据
        
        Args:
            token: JWT Token
            required_type: 需要的Token类型
            
        Returns:
            Token的解码数据
        """
        payload = self._decode_token(token)
        
        if payload.get("type") != required_type:
            if required_type == "access":
                raise AccessTokenRequired("仅允许访问Token")
            elif required_type == "refresh":
                raise RefreshTokenRequired("仅允许刷新Token")
        
        return payload
    
    def get_token_subject(self, token: str) -> str:
        """
        获取Token的主体
        
        Args:
            token: JWT Token
            
        Returns:
            Token主体（用户ID）
        """
        payload = self._decode_token(token)
        return payload.get("sub")
    
    def extract_token_from_request(self, request: Request) -> Optional[str]:
        """
        从请求中提取Token
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Token字符串或None
        """
        self._request = request
        
        # 从Header中提取
        if "headers" in self.config.token_location:
            auth_header = request.headers.get(self.config.header_name)
            if auth_header:
                parts = auth_header.split()
                if len(parts) == 2 and parts[0] == self.config.header_type:
                    self._token = parts[1]
                    return self._token
        
        return None
    
    def get_current_token(self) -> Optional[str]:
        """获取当前Token"""
        return self._token
    
    def require_auth(self, request: Request) -> Dict:
        """
        要求认证并返回Token数据
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Token的解码数据
        """
        token = self.extract_token_from_request(request)
        
        if not token:
            raise MissingTokenError("缺少认证Token")
        
        return self.verify_token(token, required_type="access")
