import request from './request'

// 记忆类型定义
export interface Memory {
  memory_id: string
  content: string
  memory_type: string
  source_dialog_id: string
  created_at: number | null
}

export interface MemoryListResponse {
  total: number
  items: Memory[]
}

export interface MemoryCreateRequest {
  content: string
  memory_type: string
}

export interface MemoryUpdateRequest {
  content?: string
  memory_type?: string
}

// 获取记忆列表
export const getMemoryList = () => {
  return request.get<MemoryListResponse>('/memory/')
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
