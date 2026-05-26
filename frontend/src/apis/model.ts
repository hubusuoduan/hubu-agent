import request from './request'

// 模型信息
export interface ModelInfo {
  id: string
  name: string
  model: string
  is_default: boolean
  is_current: boolean
}

// 获取当前模型
export const getCurrentModel = () => {
  return request.get<{ id: string; name: string; model: string; is_default: boolean }>('/model/current')
}

// 获取所有模型列表
export const getModelList = () => {
  return request.get<{ models: ModelInfo[]; current: string }>('/model/list')
}

// 切换模型
export const switchModel = (providerId: string) => {
  return request.post<{ success: boolean; current: { id: string; name: string; model: string } }>('/model/switch', { provider_id: providerId })
}
