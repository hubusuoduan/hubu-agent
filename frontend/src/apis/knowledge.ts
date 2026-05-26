import request from './request'

// 知识库类型定义
export interface KnowledgeCreate {
  name: string
  description?: string
}

export interface Knowledge {
  id: string
  name: string
  description?: string
  user_id?: string
}

export interface KnowledgeListResponse {
  total: number
  items: Knowledge[]
}

// 文件类型定义
export interface KnowledgeFile {
  id: string
  file_name: string
  knowledge_id: string
  status: string
  file_size: number
}

// RAG 查询类型定义
export interface RAGQueryRequest {
  query: string
  knowledge_ids: string[]
  top_k?: number
  min_score?: number
}

export interface RAGQueryResponse {
  query: string
  result: string
  document_count: number
}

// 创建知识库
export const createKnowledge = (data: KnowledgeCreate) => {
  return request.post<Knowledge>('/knowledge/', data)
}

// 获取知识库列表
export const getKnowledgeList = (skip = 0, limit = 10) => {
  return request.get<KnowledgeListResponse>('/knowledge/', { params: { skip, limit } })
}

// 获取知识库详情
export const getKnowledgeDetail = (knowledgeId: string) => {
  return request.get<Knowledge>(`/knowledge/${knowledgeId}`)
}

// 删除知识库
export const deleteKnowledge = (knowledgeId: string) => {
  return request.delete(`/knowledge/${knowledgeId}`)
}

// 上传文件到知识库
export const uploadFile = (knowledgeId: string, file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return request.post<KnowledgeFile>(`/knowledge/upload?knowledge_id=${knowledgeId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取知识库文件列表
export const getKnowledgeFiles = (knowledgeId: string) => {
  return request.get<{ total: number; items: KnowledgeFile[] }>(`/knowledge/${knowledgeId}/files`)
}

// 删除知识库文件（同时删除关联的向量数据）
export const deleteKnowledgeFile = (knowledgeId: string, fileId: string) => {
  return request.delete<{ message: string }>(`/knowledge/${knowledgeId}/files/${fileId}`)
}

// 更新知识库信息
export const updateKnowledge = (knowledgeId: string, data: KnowledgeCreate) => {
  return request.put<Knowledge>(`/knowledge/${knowledgeId}`, data)
}

// RAG 查询
export const ragQuery = (data: RAGQueryRequest) => {
  return request.post<RAGQueryResponse>('/knowledge/query', data)
}
