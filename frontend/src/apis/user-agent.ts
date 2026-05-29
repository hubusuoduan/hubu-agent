import request from './request'

// 用户自建 Agent 类型定义
export interface UserAgentInfo {
  id: number
  user_id: number
  name: string
  display_name: string
  description: string
  tools: string[]
  enabled: number
  create_time: string | null
  update_time: string | null
}

export interface UserAgentListResponse {
  total: number
  items: UserAgentInfo[]
}

export interface UserAgentCreateRequest {
  name: string
  display_name: string
  description: string
  system_prompt: string
  tools: string[]
}

export interface UserAgentUpdateRequest {
  display_name?: string
  description?: string
  system_prompt?: string
  tools?: string[]
  enabled?: number
}

export interface ToolInfo {
  name: string
  description: string
}

export interface ToolListResponse {
  tools: ToolInfo[]
}

// 获取用户自建 Agent 列表
export const getUserAgentList = () => {
  return request.get<UserAgentListResponse>('/user_agent/')
}

// 获取用户自建 Agent 详情
export const getUserAgent = (agentId: number) => {
  return request.get<UserAgentInfo>(`/user_agent/${agentId}`)
}

// 创建用户自建 Agent
export const createUserAgent = (data: UserAgentCreateRequest) => {
  return request.post<UserAgentInfo>('/user_agent/', data)
}

// 更新用户自建 Agent
export const updateUserAgent = (agentId: number, data: UserAgentUpdateRequest) => {
  return request.put<UserAgentInfo>(`/user_agent/${agentId}`, data)
}

// 删除用户自建 Agent
export const deleteUserAgent = (agentId: number) => {
  return request.delete<{ message: string }>(`/user_agent/${agentId}`)
}

// 获取可用工具列表
export const getAvailableTools = () => {
  return request.get<ToolListResponse>('/user_agent/tools/list')
}
