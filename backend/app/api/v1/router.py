from fastapi import APIRouter
from app.api.v1 import chat, knowledge, auth, report, dialog, memory, export

router = APIRouter()

# 注册各个模块的路由
router.include_router(chat.router, prefix="/chat", tags=["聊天"])
router.include_router(dialog.router, prefix="/dialog", tags=["对话"])
router.include_router(knowledge.router, tags=["知识库"])
router.include_router(auth.router, tags=["认证"])
router.include_router(report.router, tags=["报告"])
router.include_router(memory.router, tags=["长期记忆"])
router.include_router(export.router, prefix="/export", tags=["导出"])
