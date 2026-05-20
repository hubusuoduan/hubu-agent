from datetime import timedelta
from typing import Optional, Union, List, Set
from pydantic import BaseModel, field_validator
from datetime import timedelta


class AuthConfig(BaseModel):
    """JWT认证配置"""
    # JWT基础配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    
    # Token过期时间
    access_token_expires: timedelta = timedelta(minutes=30)
    refresh_token_expires: timedelta = timedelta(days=7)
    
    # Token存储位置
    token_location: Set[str] = {"headers"}
    
    # Header配置
    header_name: str = "Authorization"
    header_type: str = "Bearer"
    
    # Cookie配置（可选）
    access_cookie_key: str = "access_token_cookie"
    refresh_cookie_key: str = "refresh_token_cookie"
    cookie_domain: Optional[str] = None
    cookie_secure: bool = False
    
    @field_validator('algorithm')
    @classmethod
    def validate_algorithm(cls, v):
        allowed = {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512"}
        if v not in allowed:
            raise ValueError(f"Algorithm must be one of {allowed}")
        return v
    
    @field_validator('token_location', mode='before')
    @classmethod
    def validate_token_location(cls, v):
        allowed = {"headers", "cookies"}
        if isinstance(v, set):
            for loc in v:
                if loc not in allowed:
                    raise ValueError(f"Token location must be one of {allowed}")
        return v
