from fastapi import APIRouter
from app.api.v1 import chat, knowledge, auth

router = APIRouter()

# 注册各个模块的路由
router.include_router(chat.router, prefix="/chat", tags=["聊天"])
router.include_router(knowledge.router, tags=["知识库"])
router.include_router(auth.router, tags=["认证"])
