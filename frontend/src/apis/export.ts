
import request from './request'
import { fetchWithTokenRefresh, getAccessToken } from './auth'

/** 导出格式 */
export type ExportFormat = 'markdown'

/** 导出范围 */
export type ExportRange = 'all' | 'recent' | 'custom'

/** 导出请求参数 */
export interface ExportDialogParams {
  format: ExportFormat
  range: ExportRange
  recent_count?: number
  start_index?: number
  end_index?: number
}

/**
 * 导出对话
 * 使用 fetch 直接下载文件（因为 axios 不方便处理 blob 响应）
 */
export const exportDialog = async (dialogId: string, params: ExportDialogParams): Promise<void> => {
  const token = getAccessToken()

  const response = await fetchWithTokenRefresh('/api/v1/export/' + dialogId + '/export', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(params)
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: '导出失败' }))
    throw new Error(errorData.detail || '导出失败')
  }

  // 从响应头获取文件名
  const disposition = response.headers.get('Content-Disposition') || ''
  let filename = '对话导出'
  const filenameMatch = disposition.match(/filename\*?=UTF-8''(.+?)(?:;|$)/)
  if (filenameMatch) {
    filename = decodeURIComponent(filenameMatch[1])
  } else {
    const simpleMatch = disposition.match(/filename="?(.+?)"?(?:;|$)/)
    if (simpleMatch) {
      filename = simpleMatch[1]
    }
  }

  // 下载文件
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
