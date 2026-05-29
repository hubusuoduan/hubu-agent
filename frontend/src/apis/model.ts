import request from './request'

// Provider 信息
export interface ProviderInfo {
  id: number
  model: string
  enable: boolean
}

// Provider 详情（编辑用，含脱敏 api_key 和完整 base_url）
export interface ProviderDetail {
  id: number
  api_key: string  // 脱敏后的，如 sk-****1234
  base_url: string
  model: string
  enable: boolean
}

// 获取当前启用的模型
export const getCurrentModel = () => {
  return request.get<{ id: number; model: string; enable: boolean }>('/model/current')
}

// 获取用户所有模型列表
export const getModelList = () => {
  return request.get<{ models: ProviderInfo[] }>('/model/list')
}

// ===== Provider 管理 API =====

// 获取用户所有 Provider 列表
export const getProviderList = () => {
  return request.get<{ providers: ProviderInfo[] }>('/provider/list')
}

// 获取当前启用的 Provider
export const getEnabledProvider = () => {
  return request.get<{ provider: ProviderInfo | null }>('/provider/enabled')
}

// 创建 Provider
export const createProvider = (data: { api_key: string; base_url: string; model: string; enable?: boolean }) => {
  return request.post<{ success: boolean; provider: ProviderInfo }>('/provider', data)
}

// 更新 Provider
export const updateProvider = (id: number, data: { api_key?: string; base_url?: string; model?: string; enable?: boolean }) => {
  return request.put<{ success: boolean; provider: ProviderInfo }>(`/provider/${id}`, data)
}

// 删除 Provider
export const deleteProvider = (id: number) => {
  return request.delete<{ success: boolean }>(`/provider/${id}`)
}

// 启用 Provider（互斥，自动关闭其他）
export const enableProvider = (id: number) => {
  return request.post<{ success: boolean; provider: ProviderInfo }>(`/provider/${id}/enable`)
}

// 获取 Provider 详情（编辑用，api_key脱敏，base_url完整）
export const getProviderDetail = (id: number) => {
  return request.get<ProviderDetail>(`/provider/${id}/detail`)
}
