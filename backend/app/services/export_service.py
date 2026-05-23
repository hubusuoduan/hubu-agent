
"""对话导出服务"""
import re
from datetime import datetime
from typing import List

from loguru import logger

from app.database.dao.dialog_dao import DialogDao
from app.database.dao.history_dao import HistoryDao
from app.database.models.history import HistoryTable
from app.database.models.dialog import DialogTable
from app.schemas.export import ExportFormat, ExportRange, ExportDialogRequest


class ExportService:
    """对话导出服务"""

    @classmethod
    async def export_dialog(
        cls,
        dialog_id: str,
        request: ExportDialogRequest,
        user_id: int
    ) -> tuple[bytes, str, str]:
        """
        导出对话

        Args:
            dialog_id: 对话ID
            request: 导出请求
            user_id: 用户ID

        Returns:
            (文件内容bytes, 文件名, Content-Type)
        """
        # 获取对话信息
        dialog = await DialogDao.get_dialog_by_id(dialog_id)
        if not dialog:
            raise ValueError("对话不存在")
        if dialog.user_id != user_id:
            raise PermissionError("无权访问该对话")

        # 获取所有历史消息
        all_histories = await HistoryDao.get_history_by_dialog_id(dialog_id, limit=10000)

        # 根据导出范围筛选消息
        histories = cls._filter_histories(all_histories, request)

        # 生成文件名
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', dialog.name or '对话')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if request.format == ExportFormat.markdown:
            content = cls._generate_markdown(dialog, histories)
            filename = f"{safe_name}_{timestamp}.md"
            content_type = "text/markdown; charset=utf-8"
            return content.encode('utf-8'), filename, content_type


        else:
            raise ValueError(f"不支持的导出格式: {request.format}")

    @classmethod
    def _filter_histories(
        cls,
        all_histories: List[HistoryTable],
        request: ExportDialogRequest
    ) -> List[HistoryTable]:
        """根据导出范围筛选消息"""
        if request.range == ExportRange.all:
            return all_histories
        elif request.range == ExportRange.recent:
            count = request.recent_count or 20
            return all_histories[-count:] if len(all_histories) > count else all_histories
        elif request.range == ExportRange.custom:
            start = request.start_index or 0
            end = request.end_index or len(all_histories)
            return all_histories[start:end]
        return all_histories

    @classmethod
    def _generate_markdown(
        cls,
        dialog: DialogTable,
        histories: List[HistoryTable]
    ) -> str:
        """生成Markdown内容"""
        lines = []

        # 标题
        lines.append(f'# {dialog.name or "对话"}')
        lines.append("")
        lines.append("---")
        lines.append("")

        # 消息内容
        for h in histories:
            role_label = '🧑 用户' if h.role == 'user' else '🤖 AI助手' if h.role == 'assistant' else '系统'

            lines.append(f"### {role_label}")
            lines.append("")

            content = h.content or ""
            lines.append(content)
            lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

