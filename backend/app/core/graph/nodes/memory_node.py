"""长期记忆检索节点 - 从 Milvus 检索用户相关记忆"""
from loguru import logger

from app.core.graph.state import ChatState
from app.services.memory_service import get_memory_service
from app.services.settings_service import SettingsFactory


async def memory_node(state: ChatState) -> dict:
    """长期记忆检索节点

    根据用户输入，从 Milvus 中检索相关的长期记忆，
    将结果追加到 state 的 context 字段中。

    Args:
        state: Graph 状态

    Returns:
        更新后的状态字典，context 中追加了记忆信息
    """
    try:
        user_input = state.get("user_input", "")

        # 从 ContextVar 获取 user_id
        from app.middleware.user_context import current_user_id
        user_id = current_user_id.get()

        # 如果没有 user_id，跳过记忆检索
        if not user_id:
            logger.warning("未提供 user_id，跳过长期记忆检索")
            return {"memory_context": None}

        # 检索相关记忆
        memory_top_k = SettingsFactory.get(key="MEMORY_TOP_K")
        memory_min_score = SettingsFactory.get(key="MEMORY_MIN_SCORE")
        memory_service = get_memory_service()
        memories = await memory_service.search_memories(
            user_id=str(user_id),
            query=user_input,
            top_k=memory_top_k,
            min_score=memory_min_score
        )

        if not memories:
            logger.info("未检索到相关长期记忆")
            return {"memory_context": None}

        # 按 importance 降序排序，高重要性记忆优先
        memories.sort(key=lambda m: m.get("importance", 3), reverse=True)

        # 构建记忆文本
        memory_lines = []
        for m in memories:
            type_label = {
                "preference": "偏好",
                "fact": "事实",
                "insight": "洞察"
            }.get(m["memory_type"], "信息")
            memory_lines.append(f"- [{type_label}] {m['content']}")

        memory_text = "\n".join(memory_lines)
        memory_context = f"【用户长期记忆】\n{memory_text}"

        logger.info(f"长期记忆检索成功，检索到 {len(memories)} 条记忆")
        return {"memory_context": memory_context}

    except Exception as e:
        logger.error(f"长期记忆检索节点执行失败: {e}")
        # 失败时不影响主流程，返回空 memory_context
        return {"memory_context": None}
