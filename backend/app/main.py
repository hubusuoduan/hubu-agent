from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化日志配置
    setup_logging()

    # 启动时执行
    logger.info("正在启动 Hubu Agent...")
    logger.info(f"服务器配置: {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库表
    try:
        from app.database.init_db import init_db
        await init_db()
        logger.info("数据库表初始化完成")
    except Exception as e:
        logger.error(f"数据库表初始化失败: {e}")



    
    yield
    
    # 关闭时执行
    logger.info("正在关闭 Hubu Agent...")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 请求结束后清理用户配置缓存
    class SettingsCleanupMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            try:
                from app.services.settings_service import SettingsFactory
                SettingsFactory.clear_user()
            except Exception:
                pass
            try:
                from app.services.llm_service import LLMService
                LLMService.clear_user()
            except Exception:
                pass
            return response

    app.add_middleware(SettingsCleanupMiddleware)

    # 用户上下文中间件：统一解析 Token 存入 ContextVar
    from app.middleware.user_context import UserContextMiddleware
    app.add_middleware(UserContextMiddleware)

    # 注册路由
    from app.api.v1.router import router as api_router
    app.include_router(api_router, prefix="/api/v1")
    
    # 健康检查端点
    @app.get("/health")
    def health_check():
        return {"status": "ok", "version": settings.APP_VERSION}
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        reload_dirs=["app"],
    )
