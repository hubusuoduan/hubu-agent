import request from './request'

// Embedding Provider 信息（简要，隐藏 api_key）
export interface EmbeddingProviderInfo {
  id: number
  model: string
}

// Embedding Provider 详情（编辑用，api_key 脱敏，base_url 完整）
export interface EmbeddingProviderDetail {
  id: number
  api_key: string  // 脱敏后的，如 sk-****1234
  base_url: string
  model: string
}

// 获取当前用户的 Embedding Provider
export const getEmbeddingProvider = () => {
  return request.get<{ provider: EmbeddingProviderInfo | null }>('/embedding-provider')
}

// 获取 Embedding Provider 详情（编辑用，api_key 脱敏）
export const getEmbeddingProviderDetail = () => {
  return request.get<{ provider: EmbeddingProviderDetail | null }>('/embedding-provider/detail')
}

// 创建 Embedding Provider（每用户仅一条，已存在则更新）
export const createEmbeddingProvider = (data: { api_key: string; base_url?: string; model?: string }) => {
  return request.post<{ success: boolean; provider: EmbeddingProviderInfo }>('/embedding-provider', data)
}

// 更新 Embedding Provider
export const updateEmbeddingProvider = (data: { api_key?: string; base_url?: string; model?: string }) => {
  return request.put<{ success: boolean; provider: EmbeddingProviderInfo }>('/embedding-provider', data)
}

// 删除 Embedding Provider
export const deleteEmbeddingProvider = () => {
  return request.delete<{ success: boolean }>('/embedding-provider')
}
