"""Token 使用量采集 Callback - 基于 LangChain BaseCallbackHandler"""
from contextvars import ContextVar
from typing import Any
from loguru import logger
from langchain_core.callbacks import BaseCallbackHandler

# ContextVar 用于在请求级别传递 user_id
current_user_id: ContextVar[str] = ContextVar("current_user_id", default="")


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

            input_tokens = usage_metadata.get("input_tokens", 0)
            output_tokens = usage_metadata.get("output_tokens", 0)

            if input_tokens == 0 and output_tokens == 0:
                return

            # 提取模型名称
            model_name = ""
            if hasattr(response, "llm_output") and response.llm_output:
                model_name = response.llm_output.get("model_name", "")
            if not model_name:
                # 从 message 的 response_metadata 中获取
                resp_meta = getattr(message, "response_metadata", {})
                model_name = resp_meta.get("model_name", "") or resp_meta.get("model", "")

            # 通过 ContextVar 获取 user_id
            user_id = current_user_id.get("")

            # 使用同步引擎直接写入数据库
            # Callback 是同步方法，不适合 await，用同步引擎更可靠
            from app.database.engine import engine as sync_engine
            from sqlmodel import Session
            from app.database.models.usage_stats import UsageStatsTable

            record = UsageStatsTable(
                user_id=user_id,
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            with Session(sync_engine) as session:
                session.add(record)
                session.commit()

            logger.debug(
                f"Token 采集: model={model_name}, "
                f"input={input_tokens}, output={output_tokens}, user={user_id[:8] if user_id else 'unknown'}"
            )

        except Exception as e:
            logger.error(f"Token 采集失败: {e}")


# 全局 Callback 实例（复用）
usage_metadata_callback = UsageMetadataCallback()
