"""知识库检索工具 - 从企业私有文档或本地知识库中检索上下文"""
from typing import List
from loguru import logger
from langchain.tools import tool

from app.config import settings


@tool(parse_docstring=True)
async def knowledge_search(query: str, knowledge_ids: str, top_k: int = 5) -> str:
    """
    从知识库中检索与查询相关的文档内容。当需要查找企业私有文档、本地知识库中的信息时调用此工具，例如公司规章制度、产品文档、技术手册等。

    Args:
        query (str): 检索查询文本，描述你想查找的信息。
        knowledge_ids (str): 知识库ID列表，多个ID用英文逗号分隔（如 "kb_001,kb_002"）。
        top_k (int): 每个知识库返回的最大文档数量，默认为5。

    Returns:
        str: 检索到的相关文档内容，按相关性排序。

    Examples:
        - "公司年假制度是什么？" -> 调用此工具，knowledge_ids为公司制度知识库ID
        - "查找产品使用手册中关于安装的说明" -> 调用此工具
        - "技术文档里怎么配置数据库连接？" -> 调用此工具
    """
    return await _search_knowledge(query, knowledge_ids, top_k)


async def _search_knowledge(query: str, knowledge_ids: str, top_k: int = 5) -> str:
    """执行知识库检索"""

    # 参数校验
    if not query or not query.strip():
        return "查询内容不能为空"

    query = query.strip()

    if not knowledge_ids or not knowledge_ids.strip():
        return "知识库ID不能为空，请至少指定一个知识库ID"

    # 解析知识库ID列表
    ids = [kid.strip() for kid in knowledge_ids.split(",") if kid.strip()]
    if not ids:
        return "知识库ID格式无效，请使用逗号分隔多个ID（如 'kb_001,kb_002'）"

    # 限制top_k范围
    if top_k <= 0:
        top_k = settings.RAG_TOP_K
    elif top_k > 20:
        top_k = 20
        logger.warning(f"top_k超过最大值20，已自动调整为20")

    try:
        from app.services.rag.handler import RagHandler

        result = await RagHandler.query(
            query=query,
            knowledge_ids=ids,
            top_k=top_k
        )

        if not result or result.strip() == "未找到相关文档。":
            ids_str = "、".join(ids)
            return f"在知识库 [{ids_str}] 中未找到与「{query}」相关的文档内容。\n\n建议：\n1. 尝试使用不同的关键词重新检索\n2. 检查知识库ID是否正确\n3. 确认知识库中是否已上传相关文档"

        # 构建最终结果
        header = f"📚 知识库检索结果 (查询: {query})"
        source = f"📖 来源知识库: {', '.join(ids)}"
        separator = "─" * 40

        final_result = f"{header}\n{source}\n{separator}\n\n{result}"
        return final_result

    except Exception as e:
        logger.error(f"知识库检索工具执行错误: {e}")
        return f"知识库检索失败: {str(e)}"
