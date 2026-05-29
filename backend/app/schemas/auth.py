"""认证相关的 Schema"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=6, max_length=128, description="密码")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    nickname: Optional[str] = Field(default=None, max_length=50, description="昵称")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(description="访问Token")
    refresh_token: str = Field(description="刷新Token")
    token_type: str = Field(default="Bearer", description="Token类型")


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    email: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: int = Field(default=0, description="用户角色: 0=普通用户, 1=管理员")
    is_active: bool


class UpdateProfile(BaseModel):
    """更新个人信息请求"""
    email: Optional[EmailStr] = Field(default=None, description="新邮箱")
    nickname: Optional[str] = Field(default=None, max_length=50, description="新昵称")


class ChangePassword(BaseModel):
    """修改密码请求"""
    old_password: str = Field(min_length=6, max_length=128, description="旧密码")
    new_password: str = Field(min_length=6, max_length=128, description="新密码")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(description="刷新Token")
