
import request from './request'

/** 日志文件项 */
export interface LogItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  size_text?: string
  format?: string
  modify_time?: string
}

/** 日志文件列表响应 */
export interface LogListResponse {
  items: LogItem[]
  path: string
  total: number
  page: number
  page_size: number
  total_pages: number
}

/** 日志文件内容响应 */
export interface LogContentResponse {
  path: string
  name: string
  total_lines: number
  showing_lines: number
  tail: number
  content: string
}

/** 获取日志文件列表（分页） */
export async function getLogList(
  path: string = '',
  page: number = 1,
  pageSize: number = 20
): Promise<LogListResponse> {
  return request.get('/logs/list', {
    params: { path, page, page_size: pageSize }
  })
}

/** 读取日志文件内容 */
export async function readLogFile(
  filePath: string,
  tail: number = 500
): Promise<LogContentResponse> {
  return request.get(`/logs/read/${filePath}`, {
    params: { tail }
  })
}

/** 删除日志文件 */
export async function deleteLogFile(filePath: string): Promise<{ message: string; path: string }> {
  return request.delete(`/logs/delete/${filePath}`)
}
