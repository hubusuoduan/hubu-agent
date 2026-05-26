from fastapi import APIRouter
from app.api.v1 import chat, knowledge, auth, dialog, memory, export, model, workspace, skills, settings, usage_stats, logs

router = APIRouter()

# 注册各个模块的路由
router.include_router(chat.router, prefix="/chat", tags=["聊天"])
router.include_router(dialog.router, prefix="/dialog", tags=["对话"])
router.include_router(knowledge.router, tags=["知识库"])
router.include_router(auth.router, tags=["认证"])

router.include_router(memory.router, tags=["长期记忆"])
router.include_router(export.router, prefix="/export", tags=["导出"])
router.include_router(model.router, prefix="/model", tags=["模型管理"])
router.include_router(workspace.router, tags=["工作区文件"])
router.include_router(skills.router, tags=["技能管理"])
router.include_router(settings.router, prefix="/settings", tags=["系统配置"])
router.include_router(usage_stats.router, prefix="/usage_stats", tags=["Token统计"])
router.include_router(logs.router, tags=["日志查看"])
