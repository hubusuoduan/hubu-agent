import asyncio

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional, List
from loguru import logger
import json
import os
import tempfile

from app.core.graph.graph import run_stream_chat_graph_with_trace
from app.core.graph.nodes.memory_extract_node import memory_extract_node
from app.database.dao.history_dao import HistoryDao
from app.database.dao.dialog_dao import DialogDao
from app.database.session import get_async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.dependencies import get_current_user
from app.database.models.user import User
from app.schemas.chat import ChatMessage, TruncatedMessage
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/upload-file", summary="上传并解析文件")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件并解析内容

    - **file**: 上传的文件

    返回解析后的文本内容
    """
    try:
        # 支持的扩展名
        allowed_extensions = {
            '.txt', '.md', '.pdf', '.docx',  # 文本文档
            '.html', '.htm',  # 网页文件
            '.csv', '.json', '.xml',  # 数据文件
            '.xlsx',  # Excel表格
            '.pptx',  # PowerPoint演示文稿
            '.rtf',  # 富文本格式
        }
        # os.path.splitext 返回 (filename, extension), [1] 是扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            supported_formats = ', '.join(sorted(allowed_extensions))
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}。支持格式: {supported_formats}"
            )

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            # 读取上传的文件内容
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # 使用文档解析器解析文件
            from app.utils.doc_parser import SimpleDocParser

            chunks = SimpleDocParser.parse_file(tmp_file_path)

            if not chunks:
                raise HTTPException(status_code=400, detail="文件解析失败或文件为空")

            # 合并所有文本块
            full_content = "\n\n".join(chunks)

            logger.info(f"文件 {file.filename} 解析成功，共 {len(chunks)} 个文本块，{len(full_content)} 字符")

            return {
                "filename": file.filename,
                "content": full_content
            }

        finally:
            # 删除临时文件
            try:
                os.remove(tmp_file_path)
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/stream-message", summary="发送聊天消息（流式输出）")
async def send_stream_message(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    发送聊天消息（流式输出，需要认证）

    - **message**: 用户发送的消息
    - **dialog_id**: 对话ID（可选，为空则自动创建新对话）

    以 SSE 格式流式返回 AI 的回复
    """
    try:
        # 获取或创建对话
        dialog_id = chat_message.dialog_id
        if not dialog_id:
            # 自动创建新对话，用消息前20字作为名称
            name = chat_message.message[:20] + ("..." if len(chat_message.message) > 20 else "")
            dialog = await DialogDao.create_dialog(name=name, user_id=current_user.id)
            dialog_id = dialog.dialog_id
        else:
            # 校验对话存在且属于当前用户
            dialog = await DialogDao.get_dialog_by_id(dialog_id)
            if not dialog:
                raise HTTPException(status_code=404, detail="对话不存在")
            if dialog.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权访问该对话")

        # 保存用户消息到数据库（包含文件信息）
        try:
            db_content = chat_message.message
            if chat_message.file_content:
                db_content = f"[上传了文件]\n{chat_message.message}"
            await HistoryDao.create_history(
                dialog_id=dialog_id,
                role="user",
                content=db_content
            )
        except Exception as db_error:
            logger.warning(f"保存用户消息失败: {db_error}")

        # 加载历史消息（最近10条）并转换为 LangChain 消息格式
        try:
            histories = await HistoryDao.get_recent_messages(
                dialog_id=dialog_id,
                k=10
            )
            from langchain_core.messages import HumanMessage, AIMessage
            messages = []
            for h in histories:
                if h.role == "user":
                    messages.append(HumanMessage(content=h.content))
                elif h.role == "assistant":
                    messages.append(AIMessage(content=h.content))
        except Exception as db_error:
            logger.warning(f"加载历史消息失败: {db_error}")
            messages = []

        # 构建用户输入（包含文件内容）
        user_input = chat_message.message
        if chat_message.file_content:
            user_input = f"以下是文件内容：\n\n{chat_message.file_content}\n\n---\n\n{chat_message.message}"

        # 定义异步生成器函数 - 使用封装的 run_stream_chat_graph
        async def generate_stream():
            full_response = ""
            try:
                # 尽早发送 dialog_id，让前端在停止生成时能保存截断消息
                init_data = json.dumps({"type": "dialog_init", "dialog_id": dialog_id}, ensure_ascii=False)
                yield f"data: {init_data}\n\n"

                # 设置 ContextVar，让 Token 采集 Callback 能获取 user_id
                from app.callbacks import current_user_id
                current_user_id.set(str(current_user.id))

                # 使用带节点追踪的流式 Graph 函数
                async for event in run_stream_chat_graph_with_trace(
                    user_input=user_input,
                    session_id=dialog_id,
                    user_id=current_user.id,
                    messages=messages
                ):
                    if isinstance(event, dict):
                        event_type = event.get("type", "")
                        if event_type == "content":
                            full_response += event.get("content", "")
                        # 将所有结构化事件（含节点追踪）发送给前端
                        data = json.dumps(event, ensure_ascii=False)
                        yield f"data: {data}\n\n"

                # 保存完整的 AI 回复到数据库
                try:
                    await HistoryDao.create_history(
                        dialog_id=dialog_id,
                        role="assistant",
                        content=full_response
                    )
                except Exception as db_error:
                    logger.warning(f"保存AI回复失败: {db_error}")

                logger.info(f"流式输出完成，总长度: {len(full_response)}")

                # 异步触发记忆提取（不阻塞响应）
                async def _do_extract():
                    try:
                        state = {
                            "messages": messages,
                            "user_input": user_input,
                            "context": None,
                            "session_id": dialog_id,
                            "user_id": current_user.id,
                            "response": full_response
                        }
                        await memory_extract_node(state)
                    except Exception as e:
                        logger.error(f"异步记忆提取失败: {e}")

                asyncio.create_task(_do_extract())

                # 发送结束标记，附带 dialog_id
                done_data = json.dumps({"done": True, "dialog_id": dialog_id}, ensure_ascii=False)
                yield f"data: {done_data}\n\n"

            except Exception as e:
                logger.error(f"流式处理消息失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理流式消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理流式消息失败: {str(e)}")


@router.post("/save-truncated", summary="保存被截断的AI消息")
async def save_truncated_message(
    truncated: TruncatedMessage,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    当用户停止生成时，前端将已接收的AI消息内容通过此接口保存到后端。

    - **dialog_id**: 对话ID
    - **content**: 被截断的AI消息内容
    """
    try:
        # 校验对话存在且属于当前用户
        dialog = await DialogDao.get_dialog_by_id(truncated.dialog_id)
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在")
        if dialog.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问该对话")

        # 保存截断的AI消息
        history = await HistoryDao.create_history(
            dialog_id=truncated.dialog_id,
            role="assistant",
            content=truncated.content
        )
        logger.info(f"保存截断消息成功: dialog_id={truncated.dialog_id}, 长度={len(truncated.content)}")
        return {"id": history.id, "dialog_id": truncated.dialog_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存截断消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存截断消息失败: {str(e)}")

