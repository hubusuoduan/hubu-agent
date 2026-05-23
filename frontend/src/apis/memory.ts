import request from './request'

// 记忆类型定义
export interface Memory {
  memory_id: string
  content: string
  memory_type: string
  source_dialog_id: string
  created_at: number | null
  importance: number
}

export interface MemoryListResponse {
  total: number
  items: Memory[]
}

export interface MemoryCreateRequest {
  content: string
  memory_type: string
  importance?: number
}

export interface MemoryUpdateRequest {
  content?: string
  memory_type?: string
  importance?: number
}

// 获取记忆列表（支持分页和搜索）
export const getMemoryList = (params?: {
  page?: number
  page_size?: number
  keyword?: string
  memory_type?: string
}) => {
  return request.get<MemoryListResponse>('/memory/', { params })
}

// 手动添加记忆
export const createMemory = (data: MemoryCreateRequest) => {
  return request.post<Memory>('/memory/', data)
}

// 更新记忆
export const updateMemory = (memoryId: string, data: MemoryUpdateRequest) => {
  return request.put<Memory>(`/memory/${memoryId}`, data)
}

// 删除记忆
export const deleteMemory = (memoryId: string) => {
  return request.delete(`/memory/${memoryId}`)
}
