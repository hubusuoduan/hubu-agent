import request from './request'
import { fetchWithTokenRefresh, getAccessToken } from './auth'

export interface ChatMessage {
  message: string
  dialog_id?: string  // 对话ID，为空则自动创建新对话
  file_content?: string  // 文件解析后的内容
}

export interface ChatResponse {
  response: string
  dialog_id: string
}

// 发送聊天消息
export const sendMessage = (data: ChatMessage) => {
  return request.post<ChatResponse>('/chat/message', data)
}

// 用于取消流式请求的控制器
let abortController: AbortController | null = null

// 发送流式聊天消息
export const sendStreamMessage = async (
  data: ChatMessage,
  onChunk: (chunk: string) => void,
  onComplete: (dialogId?: string) => void,
  onError: (error: Error) => void
) => {
  try {
    // 创建新的 AbortController
    abortController = new AbortController()

    const token = getAccessToken()

    const response = await fetchWithTokenRefresh('/api/v1/chat/stream-message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data),
      signal: abortController.signal // 添加中止信号
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Response body is null')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        onComplete()
        break
      }

      // 解码数据
      buffer += decoder.decode(value, { stream: true })

      // 处理 SSE 格式的数据
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || '' // 保留最后一个不完整的数据块

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()

          if (data === '[DONE]') {
            onComplete()
            return
          }

          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              onChunk(parsed.content)
            }
            if (parsed.done && parsed.dialog_id) {
              // 流式结束，返回 dialog_id
              onComplete(parsed.dialog_id)
            }
            if (parsed.error) {
              onError(new Error(parsed.error))
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e)
          }
        }
      }
    }
  } catch (error) {
    // 如果是用户主动取消,不报错
    if ((error as Error).name === 'AbortError') {
      console.log('流式请求已取消')
      return
    }
    onError(error as Error)
  } finally {
    abortController = null
  }
}

// 取消流式请求
export const cancelStreamMessage = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}

// 获取聊天历史
export const getChatHistory = (dialogId: string) => {
  return request.get(`/chat/history/${dialogId}`)
}

// 上传并解析文件
export const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const token = getAccessToken()

  const response = await fetchWithTokenRefresh('/api/v1/chat/upload-file', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || '文件上传失败')
  }

  return await response.json()
}

// ========== 对话管理 API ==========

export interface DialogInfo {
  dialog_id: string
  name: string
  user_id: number | null
  summary: string | null
  create_time: string | null
  update_time: string | null
}

// 创建新对话
export const createDialog = (name: string = '新对话') => {
  return request.post<{ dialog_id: string; name: string; user_id: number | null }>('/dialog/create', { name })
}

// 获取对话列表
export const getDialogList = (limit: number = 50) => {
  return request.get<{ dialogs: DialogInfo[]; total: number }>('/dialog/list', { params: { limit } })
}

// 更新对话名称
export const updateDialogName = (dialogId: string, name: string) => {
  return request.put(`/dialog/${dialogId}/name`, { name })
}

// 删除对话
export const deleteDialog = (dialogId: string) => {
  return request.delete(`/dialog/${dialogId}`)
}

// 获取对话详情
export const getDialogDetail = (dialogId: string) => {
  return request.get<DialogInfo>(`/dialog/${dialogId}`)
}

// 获取对话历史
export const getDialogHistory = (dialogId: string, limit: number = 50) => {
  return request.get(`/dialog/${dialogId}/history`, { params: { limit } })
}
