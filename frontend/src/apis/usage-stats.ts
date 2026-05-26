import request from './request'

/** Token 使用量查询参数 */
export interface UsageQuery {
  delta_days?: number  // 查询最近多少天，默认7
  model?: string       // 模型名称过滤（可选）
}

/** 按日期+模型聚合的 Token 使用量记录 */
export interface UsageRecord {
  date: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
}

/** Token 使用量汇总 */
export interface UsageSummary {
  total_input_tokens: number
  total_output_tokens: number
  total_tokens: number
}

/** Token 使用量响应 */
export interface UsageResponse {
  data: UsageRecord[]
  summary: UsageSummary
}

/** 按日期+模型聚合的调用次数记录 */
export interface UsageCountRecord {
  date: string
  model: string
  count: number
}

/** 调用次数响应 */
export interface UsageCountResponse {
  data: UsageCountRecord[]
  summary: {
    total_count: number
  }
}

/** 获取 Token 使用量（按日期+模型聚合） */
export const getUsageStats = (query: UsageQuery = {}) => {
  return request.post<UsageResponse>('/usage_stats/usage', query)
}

/** 获取调用次数（按日期+模型聚合） */
export const getUsageCount = (query: UsageQuery = {}) => {
  return request.post<UsageCountResponse>('/usage_stats/usage_count', query)
}

/** 获取用户使用过的模型列表 */
export const getModelsList = () => {
  return request.get<{ models: string[] }>('/usage_stats/models_list')
}
