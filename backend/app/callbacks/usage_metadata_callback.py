"""Token 使用量采集 Callback - 基于 LangChain BaseCallbackHandler"""
from typing import Any
from loguru import logger
from langchain_core.callbacks import BaseCallbackHandler

from app.middleware.user_context import current_user_id


class UsageMetadataCallback(BaseCallbackHandler):
    """Token 使用量采集回调

    在 LLM 调用结束时自动捕获 usage_metadata，
    通过 ContextVar 获取当前请求的 user_id，写入数据库。

    使用方式：
        callback = UsageMetadataCallback()
        config = {"callbacks": [callback]}
        agent.astream_events(..., config=config)
    """

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """LLM 调用结束时触发，提取 token 用量并写入数据库"""
        try:
            # 从 generations 中提取 usage_metadata
            if not response.generations or not response.generations[0]:
                return

            message = response.generations[0][0].message

            # 提取 token 用量
            usage_metadata = getattr(message, "usage_metadata", None)
            if not usage_metadata:
                return

            # 兼容不同格式：dict / int / 其他
            if isinstance(usage_metadata, int):
                input_tokens = 0
                output_tokens = usage_metadata
            elif isinstance(usage_metadata, dict):
                input_tokens = usage_metadata.get("input_tokens", 0)
                output_tokens = usage_metadata.get("output_tokens", 0)
            else:
                # 尝试属性访问（LangChain UsageMetadata 对象）
                input_tokens = getattr(usage_metadata, "input_tokens", 0)
                output_tokens = getattr(usage_metadata, "output_tokens", 0)

            if input_tokens == 0 and output_tokens == 0:
                return

            # 提取模型名称
            model_name = ""
            if hasattr(response, "llm_output") and response.llm_output:
                llm_output = response.llm_output
                if isinstance(llm_output, dict):
                    model_name = llm_output.get("model_name", "")
            if not model_name:
                # 从 message 的 response_metadata 中获取
                resp_meta = getattr(message, "response_metadata", {})
                if isinstance(resp_meta, dict):
                    model_name = resp_meta.get("model_name", "") or resp_meta.get("model", "")

            # 通过 ContextVar 获取 user_id（int → str）
            user_id = current_user_id.get()
            if user_id is not None:
                user_id = str(user_id)

            # 使用同步方法累加写入：同一天同模型同用户则累加，否则新建
            from app.database.dao.usage_stats_dao import UsageStatsDao

            UsageStatsDao.upsert_usage_stats_sync(
                user_id=user_id,
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            logger.debug(
                f"Token 采集: model={model_name}, "
                f"input={input_tokens}, output={output_tokens}, user={user_id or 'unknown'}"
            )

        except Exception as e:
            logger.error(f"Token 采集失败: {e}")


# 全局 Callback 实例（复用）
usage_metadata_callback = UsageMetadataCallback()
