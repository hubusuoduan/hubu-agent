
import request from './request'

/** 工作区文件项 */
export interface WorkspaceItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  size_text?: string
  format?: string
  modify_time?: string
}

/** 工作区文件列表响应 */
export interface WorkspaceListResponse {
  items: WorkspaceItem[]
  path: string
  total: number
  page: number
  page_size: number
  total_pages: number
}

/** 获取工作区文件列表（分页） */
export async function getWorkspaceList(
  path: string = '',
  page: number = 1,
  pageSize: number = 20
): Promise<WorkspaceListResponse> {
  return request.get('/workspace/list', {
    params: { path, page, page_size: pageSize }
  })
}

/** 删除工作区文件或目录 */
export async function deleteWorkspaceFile(filePath: string): Promise<{ message: string; path: string }> {
  return request.delete(`/workspace/delete/${filePath}`)
}

/** 获取文件下载URL */
export function getWorkspaceDownloadUrl(filePath: string): string {
  const token = localStorage.getItem('access_token')
  return `/api/v1/workspace/download/${filePath}${token ? `?token=${token}` : ''}`
}
