/** 报告相关 API */
import request from './request'

/** 获取报告列表 */
export function getReportList(params?: { skip?: number; limit?: number }) {
  return request.get('/report/list', { params })
}

/** 下载报告文件 - 返回完整 URL 供浏览器下载 */
export function getReportDownloadUrl(reportId: string): string {
  const token = localStorage.getItem('access_token')
  return `/api/v1/report/download/${reportId}${token ? `?token=${token}` : ''}`
}

/** 删除报告 */
export function deleteReport(reportId: string) {
  return request.delete(`/report/${reportId}`)
}
