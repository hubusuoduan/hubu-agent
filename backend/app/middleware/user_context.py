"""用户上下文 - ContextVar 定义 + 中间件"""
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

# 当前请求的用户ID（中间件统一设置，请求结束清理）
current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)

# 不需要解析 token 的路径前缀
SKIP_PATHS = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
)


class UserContextMiddleware(BaseHTTPMiddleware):
    """请求进来时解析 JWT Token，将 user_id 存入 ContextVar，请求结束清理"""

    async def dispatch(self, request: Request, call_next):
        # 跳过不需要认证的路径
        path = request.url.path
        if any(path.startswith(skip) for skip in SKIP_PATHS):
            return await call_next(request)

        # 尝试从 Authorization header 解析 token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from app.auth.auth_jwt import JWTAuth
                from app.auth.config import AuthConfig
                jwt_auth = JWTAuth(AuthConfig())
                payload = jwt_auth.verify_token(token, required_type="access")
                user_id = payload.get("sub")
                if user_id:
                    current_user_id.set(int(user_id))
            except Exception as e:
                logger.debug(f"UserContextMiddleware: Token解析失败: {e}")

        response = await call_next(request)

        # 请求结束清理
        current_user_id.set(None)

        return response
