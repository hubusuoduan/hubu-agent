"""知识库列表查询工具 - 获取所有可用的知识库信息"""
from loguru import logger
from langchain.tools import tool


@tool(parse_docstring=True)
async def knowledge_list(keyword: str = "") -> str:
    """
    获取所有可用的知识库列表。在检索知识库内容之前，先调用此工具了解有哪些知识库可用，获取知识库的ID、名称和描述信息，以便后续使用knowledge_search工具进行检索。

    Args:
        keyword (str): 可选的搜索关键词，用于过滤知识库名称或描述中包含该关键词的知识库。为空时返回所有知识库。

    Returns:
        str: 知识库列表信息，包含每个知识库的ID、名称、描述和文件数量。

    Examples:
        - "有哪些知识库可以用？" -> 调用此工具
        - "我想查一下公司相关的知识库" -> 调用此工具，keyword="公司"
        - "帮我找找产品文档知识库" -> 调用此工具，keyword="产品"
    """
    return await _list_knowledge(keyword)


async def _list_knowledge(keyword: str = "") -> str:
    """执行知识库列表查询"""
    keyword = keyword.strip() if keyword else ""

    try:
        from sqlmodel import select, func, col
        from app.database.models import KnowledgeTable, KnowledgeFileTable
        from app.database.engine import async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        if async_engine is None:
            return "数据库未连接，无法获取知识库列表。请检查数据库配置。"

        async with AsyncSession(async_engine) as session:
            # 构建查询
            if keyword:
                statement = select(KnowledgeTable).where(
                    col(KnowledgeTable.name).contains(keyword) |
                    col(KnowledgeTable.description).contains(keyword)
                )
            else:
                statement = select(KnowledgeTable)

            result = await session.execute(statement)
            knowledge_list = result.scalars().all()

            if not knowledge_list:
                if keyword:
                    return f"未找到名称或描述中包含「{keyword}」的知识库。\n\n建议：\n1. 尝试使用其他关键词\n2. 不传关键词查看所有知识库"
                else:
                    return "当前没有任何知识库。请先通过管理后台上传文档创建知识库。"

            # 查询每个知识库的文件数量
            items = []
            for kb in knowledge_list:
                # 统计文件数量
                file_count_statement = select(func.count()).select_from(KnowledgeFileTable).where(
                    KnowledgeFileTable.knowledge_id == kb.id
                )
                file_count_result = await session.execute(file_count_statement)
                file_count = file_count_result.scalar() or 0

                # 格式化时间
                create_time = kb.create_time.strftime("%Y-%m-%d %H:%M") if kb.create_time else "未知"

                item = (
                    f"📦 知识库ID: {kb.id}\n"
                    f"   名称: {kb.name}\n"
                    f"   描述: {kb.description or '暂无描述'}\n"
                    f"   文件数: {file_count}\n"
                    f"   创建时间: {create_time}"
                )
                items.append(item)

            # 构建最终结果
            header = f"📚 知识库列表 (共 {len(knowledge_list)} 个"
            if keyword:
                header += f"，关键词: {keyword}"
            header += ")"
            separator = "─" * 40

            final_result = f"{header}\n{separator}\n\n" + f"\n\n".join(items)

            # 添加使用提示
            final_result += f"\n\n{separator}\n💡 提示: 使用 knowledge_search 工具检索知识库内容，knowledge_ids 参数填写上面的知识库ID"

            return final_result

    except Exception as e:
        logger.error(f"知识库列表查询工具执行错误: {e}")
        return f"获取知识库列表失败: {str(e)}"
