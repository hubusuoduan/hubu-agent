"""知识库相关Schema"""
from pydantic import BaseModel, Field
from typing import Optional, List


class KnowledgeCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., description="知识库名称", max_length=128)
    description: Optional[str] = Field(default=None, description="知识库描述", max_length=1024)


class KnowledgeResponse(BaseModel):
    """知识库响应"""
    id: str
    name: str
    description: Optional[str]
    user_id: Optional[str]


class KnowledgeListResponse(BaseModel):
    """知识库列表响应"""
    total: int
    items: List[KnowledgeResponse]


class KnowledgeFileUpload(BaseModel):
    """上传知识库文件请求"""
    knowledge_id: str = Field(..., description="知识库ID")
    file_name: str = Field(..., description="文件名")


class KnowledgeFileResponse(BaseModel):
    """知识库文件响应"""
    id: str
    file_name: str
    knowledge_id: str
    status: str
    file_size: int


class RAGQueryRequest(BaseModel):
    """RAG查询请求"""
    query: str = Field(..., description="查询文本")
    knowledge_ids: List[str] = Field(..., description="知识库ID列表")
    top_k: int = Field(default=5, description="返回结果数量", ge=1, le=20)
    min_score: float = Field(default=0.3, description="最小分数阈值", ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    """RAG查询响应"""
    query: str
    result: str
    document_count: int
