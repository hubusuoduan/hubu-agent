import request from './request'

// 技能类型定义
export interface SkillInfo {
  name: string
  description: string
  dir_name: string
  source: 'system' | 'user'
}

export interface SkillListResponse {
  total: number
  items: SkillInfo[]
  page: number
  page_size: number
}

export interface SkillAddRequest {
  name: string
  description?: string
  skill_md_content?: string
}

// 获取技能列表
export const getSkillList = (page = 1, pageSize = 20, keyword = '') => {
  return request.get<SkillListResponse>('/skills/list', {
    params: { page, page_size: pageSize, keyword: keyword || undefined }
  })
}

// 添加技能
export const addSkill = (data: SkillAddRequest) => {
  return request.post<{ name: string; description: string; message: string }>('/skills/add', null, {
    params: { name: data.name, description: data.description || '', skill_md_content: data.skill_md_content || undefined }
  })
}

// 上传技能包（name 和 description 从 ZIP 中的 SKILL.md 自动提取）
export const uploadSkill = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  return request.post<{ name: string; description: string; message: string }>(
    '/skills/upload',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
}

// 删除技能
export const deleteSkill = (skillName: string) => {
  return request.delete<{ message: string }>(`/skills/${encodeURIComponent(skillName)}`)
}
