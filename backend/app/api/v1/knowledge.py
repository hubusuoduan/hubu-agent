"""知识库API"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List
import tempfile
import os

from app.database.session import get_async_session
from app.database.models import KnowledgeTable, KnowledgeFileTable
from app.services.rag.handler import RagHandler
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeResponse,
    KnowledgeListResponse,
    KnowledgeFileResponse,
    RAGQueryRequest,
    RAGQueryResponse
)
from app.api.dependencies import get_current_user
from app.database.models.user import User

router = APIRouter(prefix="/knowledge", tags=["知识库"])


def _check_knowledge_owner(knowledge: KnowledgeTable, user: User):
    """检查用户是否有权操作该知识库（管理员拥有所有权限）"""
    if user.role != 1 and knowledge.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="无权操作该知识库")


@router.post("/", response_model=KnowledgeResponse, summary="创建知识库")
async def create_knowledge(
    data: KnowledgeCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """创建知识库（需要认证）"""
    # 检查知识库名称是否已存在（管理员不受限制，普通用户仅限自己名下）
    if current_user.role != 1:
        statement = select(KnowledgeTable).where(
            KnowledgeTable.name == data.name,
            KnowledgeTable.user_id == str(current_user.id)
        )
    else:
        statement = select(KnowledgeTable).where(KnowledgeTable.name == data.name)
    result = await session.execute(statement)
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="知识库名称已存在")

    # 创建知识库
    knowledge = KnowledgeTable(
        name=data.name,
        description=data.description,
        user_id=str(current_user.id)
    )
    session.add(knowledge)
    await session.commit()
    await session.refresh(knowledge)

    return KnowledgeResponse(
        id=knowledge.id,
        name=knowledge.name,
        description=knowledge.description,
        user_id=knowledge.user_id
    )


@router.get("/", response_model=KnowledgeListResponse, summary="获取知识库列表")
async def list_knowledge(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取知识库列表（需要认证，普通用户只看自己的，管理员看所有）"""
    if current_user.role == 1:
        # 管理员看所有知识库
        total_statement = select(KnowledgeTable)
        statement = select(KnowledgeTable).offset(skip).limit(limit)
    else:
        # 普通用户只看自己的
        total_statement = select(KnowledgeTable).where(KnowledgeTable.user_id == str(current_user.id))
        statement = select(KnowledgeTable).where(KnowledgeTable.user_id == str(current_user.id)).offset(skip).limit(limit)

    total_result = await session.execute(total_statement)
    total = len(total_result.scalars().all())

    result = await session.execute(statement)
    items = result.scalars().all()

    return KnowledgeListResponse(
        total=total,
        items=[KnowledgeResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            user_id=item.user_id
        ) for item in items]
    )


@router.get("/{knowledge_id}", response_model=KnowledgeResponse, summary="获取知识库详情")
async def get_knowledge(
    knowledge_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取知识库详情（需要认证，管理员可查看所有）"""
    knowledge = await session.get(KnowledgeTable, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库不存在")
    _check_knowledge_owner(knowledge, current_user)

    return KnowledgeResponse(
        id=knowledge.id,
        name=knowledge.name,
        description=knowledge.description,
        user_id=knowledge.user_id
    )


@router.delete("/{knowledge_id}", summary="删除知识库")
async def delete_knowledge(
    knowledge_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """删除知识库及其所有文件（需要认证，管理员可删除所有）"""
    knowledge = await session.get(KnowledgeTable, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库不存在")
    _check_knowledge_owner(knowledge, current_user)

    # 删除知识库下的所有文件记录
    statement = select(KnowledgeFileTable).where(KnowledgeFileTable.knowledge_id == knowledge_id)
    result = await session.execute(statement)
    files = result.scalars().all()

    # 删除数据库中的文件记录
    for file in files:
        await session.delete(file)

    # 直接删除整个 Milvus 集合（比逐条删除更高效，且能释放磁盘空间）
    from app.services.rag.milvus_client import vector_db_client
    await vector_db_client.delete_collection(knowledge_id)

    await session.delete(knowledge)
    await session.commit()

    return {"message": "删除成功"}


@router.post("/upload", response_model=KnowledgeFileResponse, summary="上传文件到知识库")
async def upload_file_to_knowledge(
    knowledge_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """上传文件到知识库并索引（需要认证，管理员可上传到所有知识库）"""
    # 检查知识库是否存在
    knowledge = await session.get(KnowledgeTable, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库不存在")
    _check_knowledge_owner(knowledge, current_user)

    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 创建文件记录（先不commit，索引成功后再提交，避免索引失败产生脏数据）
        file_record = KnowledgeFileTable(
            file_name=file.filename,
            knowledge_id=knowledge_id,
            file_size=len(content),
            user_id=str(current_user.id)
        )
        # ID由uuid4自动生成，不需要commit就能获取

        # 索引文档
        chunk_ids = await RagHandler.index_documents(
            knowledge_id=knowledge_id,
            file_id=file_record.id,
            file_name=file.filename,
            file_path=tmp_path
        )

        if not chunk_ids:
            # 索引失败，清理已写入向量存储的数据
            try:
                await RagHandler.delete_documents(file_record.id, knowledge_id)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail="文档索引失败")

        # 索引成功，提交文件记录到数据库
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)

        return KnowledgeFileResponse(
            id=file_record.id,
            file_name=file_record.file_name,
            knowledge_id=file_record.knowledge_id,
            status=file_record.status,
            file_size=file_record.file_size
        )
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/{knowledge_id}/files", summary="获取知识库文件列表")
async def list_knowledge_files(
    knowledge_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取知识库下的所有文件列表（管理员可查看所有）"""
    knowledge = await session.get(KnowledgeTable, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库不存在")
    _check_knowledge_owner(knowledge, current_user)

    statement = select(KnowledgeFileTable).where(KnowledgeFileTable.knowledge_id == knowledge_id)
    result = await session.execute(statement)
    files = result.scalars().all()

    return {
        "total": len(files),
        "items": [KnowledgeFileResponse(
            id=f.id,
            file_name=f.file_name,
            knowledge_id=f.knowledge_id,
            status=f.status,
            file_size=f.file_size
        ) for f in files]
    }


@router.delete("/{knowledge_id}/files/{file_id}", summary="删除知识库文件")
async def delete_knowledge_file(
    knowledge_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """删除知识库中的文件及其关联的向量数据（管理员可删除所有）"""
    knowledge = await session.get(KnowledgeTable, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库不存在")
    _check_knowledge_owner(knowledge, current_user)

    file_record = await session.get(KnowledgeFileTable, file_id)
    if not file_record or file_record.knowledge_id != knowledge_id:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 删除向量存储中的文档
    await RagHandler.delete_documents(file_id, knowledge_id)
    # 删除数据库记录
    await session.delete(file_record)
    await session.commit()

    return {"message": "文件删除成功"}


@router.put("/{knowledge_id}", summary="更新知识库信息")
async def update_knowledge(
    knowledge_id: str,
    data: KnowledgeCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """更新知识库名称和描述（管理员可更新所有）"""
    knowledge = await session.get(KnowledgeTable, knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识库不存在")
    _check_knowledge_owner(knowledge, current_user)

    # 检查名称是否与其他知识库冲突（管理员全局检查，普通用户限自己名下）
    if data.name != knowledge.name:
        if current_user.role != 1:
            statement = select(KnowledgeTable).where(
                KnowledgeTable.name == data.name,
                KnowledgeTable.user_id == str(current_user.id)
            )
        else:
            statement = select(KnowledgeTable).where(KnowledgeTable.name == data.name)
        result = await session.execute(statement)
        existing = result.scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="知识库名称已存在")

    knowledge.name = data.name
    knowledge.description = data.description
    session.add(knowledge)
    await session.commit()
    await session.refresh(knowledge)

    return KnowledgeResponse(
        id=knowledge.id,
        name=knowledge.name,
        description=knowledge.description,
        user_id=knowledge.user_id
    )


@router.post("/query", response_model=RAGQueryResponse, summary="RAG查询")
async def rag_query(
    data: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """RAG查询 - 从知识库中检索相关内容（需要认证，管理员可查询所有知识库）"""
    # 验证知识库是否存在，普通用户还需验证所有权
    for knowledge_id in data.knowledge_ids:
        knowledge = await session.get(KnowledgeTable, knowledge_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail=f"知识库 {knowledge_id} 不存在")
        if current_user.role != 1 and knowledge.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail=f"无权访问知识库 {knowledge_id}")

    # 执行RAG查询
    result = await RagHandler.query(
        query=data.query,
        knowledge_ids=data.knowledge_ids,
        top_k=data.top_k,
        min_score=data.min_score
    )

    # 计算返回的文档数量（简单按换行符分割）
    doc_count = len([p for p in result.split("\n\n") if p.strip()])

    return RAGQueryResponse(
        query=data.query,
        result=result,
        document_count=doc_count
    )
