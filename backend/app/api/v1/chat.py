from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
import json
import os
import tempfile

from app.core.graph.graph import run_chat_graph, run_stream_chat_graph
from app.database.dao.history_dao import HistoryDao
from app.database.session import get_async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends
from app.api.dependencies import get_current_user
from app.database.models.user import User
from fastapi.responses import StreamingResponse

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息模型"""
    message: str
    session_id: Optional[str] = None
    file_content: Optional[str] = None  # 文件解析后的内容


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    session_id: str


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
                "content": full_content,
                "chunks_count": len(chunks),
                "total_length": len(full_content)
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


@router.post("/message", response_model=ChatResponse, summary="发送聊天消息")
async def send_message(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    发送聊天消息（需要认证）
    
    - **message**: 用户发送的消息
    - **session_id**: 会话ID（可选）
    
    返回AI的回复和会话ID
    """
    try:
        session_id = chat_message.session_id or "default_session"
        
        # 保存用户消息到数据库（包含文件信息）
        try:
            db_content = chat_message.message
            if chat_message.file_content:
                db_content = f"[上传了文件]\n{chat_message.message}"
            await HistoryDao.create_history(
                dialog_id=session_id,
                role="user",
                content=db_content
            )
        except Exception as db_error:
            logger.warning(f"保存用户消息失败: {db_error}")
        
        # 加载历史消息（最近10条）并转换为 LangChain 消息格式
        try:
            histories = await HistoryDao.get_recent_messages(
                dialog_id=session_id,
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
        
        # 运行 Chat Graph（RAG 节点会自动检索所有知识库）
        graph_result = await run_chat_graph(
            user_input=user_input,
            session_id=session_id,
            messages=messages
        )
        
        response_text = graph_result.get("response", "")
        
        # 保存AI回复到数据库
        try:
            await HistoryDao.create_history(
                dialog_id=session_id,
                role="assistant",
                content=response_text
            )
        except Exception as db_error:
            logger.warning(f"保存AI回复失败: {db_error}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")


@router.post("/stream-message", summary="发送聊天消息（流式输出）")
async def send_stream_message(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    发送聊天消息（流式输出，需要认证）
    
    - **message**: 用户发送的消息
    - **session_id**: 会话ID（可选）
    
    以 SSE 格式流式返回 AI 的回复
    """
    try:
        session_id = chat_message.session_id or "default_session"
        
        # 保存用户消息到数据库（包含文件信息）
        try:
            db_content = chat_message.message
            if chat_message.file_content:
                db_content = f"[上传了文件]\n{chat_message.message}"
            await HistoryDao.create_history(
                dialog_id=session_id,
                role="user",
                content=db_content
            )
        except Exception as db_error:
            logger.warning(f"保存用户消息失败: {db_error}")
        
        # 加载历史消息（最近10条）并转换为 LangChain 消息格式
        try:
            histories = await HistoryDao.get_recent_messages(
                dialog_id=session_id,
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
                # 使用封装好的流式 Graph 函数
                async for chunk in run_stream_chat_graph(
                    user_input=user_input,
                    session_id=session_id,
                    messages=messages
                ):
                    full_response += chunk
                    data = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                
                # 保存完整的 AI 回复到数据库
                try:
                    await HistoryDao.create_history(
                        dialog_id=session_id,
                        role="assistant",
                        content=full_response
                    )
                except Exception as db_error:
                    logger.warning(f"保存AI回复失败: {db_error}")
                
                logger.info(f"流式输出完成，总长度: {len(full_response)}")
                # 发送结束标记
                yield "data: [DONE]\n\n"
                
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


@router.get("/history/{session_id}", summary="获取聊天历史")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取聊天历史（需要认证）
    
    - **session_id**: 会话ID
    - **limit**: 限制返回数量（默认50）
    """
    try:
        histories = await HistoryDao.get_history_by_dialog_id(
            dialog_id=session_id,
            limit=limit
        )
        
        messages = [
            {
                "role": h.role,
                "content": h.content,
                "create_time": h.create_time.isoformat() if h.create_time else None
            }
            for h in histories
        ]
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total": len(messages)
        }
    except Exception as e:
        logger.error(f"获取聊天历史失败: {e}")
        return {
            "session_id": session_id,
            "messages": [],
            "total": 0
        }


