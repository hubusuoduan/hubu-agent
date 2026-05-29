"""用户模型"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    """用户表模型"""
    
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="用户ID")
    username: str = Field(unique=True, index=True, max_length=50, description="用户名")
    email: Optional[str] = Field(default=None, unique=True, index=True, max_length=100, description="邮箱")
    password_hash: str = Field(max_length=255, description="密码哈希")
    nickname: Optional[str] = Field(default=None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(default=None, max_length=500, description="头像URL")
    role: int = Field(default=0, description="用户角色: 0=普通用户, 1=管理员")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
