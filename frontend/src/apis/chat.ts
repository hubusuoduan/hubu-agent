import request from './request'
import { fetchWithTokenRefresh, getValidAccessToken } from './auth'

export interface ChatMessage {
  message: string
  dialog_id?: string  // 对话ID，为空则自动创建新对话
  file_content?: string  // 文件解析后的内容
}

// 用于取消流式请求的控制器
let abortController: AbortController | null = null

// 发送流式聊天消息
// 思考过程事件类型
export interface ThinkingEvent {
  type: 'thinking'
  content?: string
}

// 工具调用事件数据
export interface ToolCallEventData {
  title: string
  status: 'START' | 'END' | 'ERROR'
  message: string
  tool_name?: string
}

// 工具调用事件
export interface ToolCallEvent {
  type: 'event'
  data: ToolCallEventData
}

// 节点追踪事件类型
export interface NodeEvent {
  type: 'node_start' | 'node_end' | 'node_error' | 'workflow_done'
  node?: string
  display_name?: string
  duration_ms?: number
  input_summary?: string
  output_summary?: string
  error?: string
  nodes?: string[]
  total_duration_ms?: number
  timestamp?: number
}

export const sendStreamMessage = async (
  data: ChatMessage,
  onChunk: (chunk: string) => void,
  onComplete: (dialogId?: string) => void,
  onError: (error: Error) => void,
  onEvent?: (event: ThinkingEvent) => void,
  onNodeEvent?: (event: NodeEvent) => void,
  onToolEvent?: (event: ToolCallEvent) => void,
  onDialogInit?: (dialogId: string) => void
) => {
  try {
    // 创建新的 AbortController
    abortController = new AbortController()

    const token = await getValidAccessToken()

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
            // 结构化事件格式：{ type: "content"|"thinking"|"event"|"node_*", ... }
            if (parsed.type) {
              if (parsed.type === 'dialog_init' && parsed.dialog_id) {
                // 尽早通知 dialog_id，让停止生成时能保存截断消息
                if (onDialogInit) onDialogInit(parsed.dialog_id)
              }
              if (parsed.type === 'content' && parsed.content) {
                onChunk(parsed.content)
              }
              // 工具调用事件通过 onToolEvent 回调传递
              else if (parsed.type === 'event' && onToolEvent) {
                onToolEvent(parsed)
              }
              // 节点追踪事件通过 onNodeEvent 回调传递
              else if (['node_start', 'node_end', 'node_error', 'workflow_done'].includes(parsed.type) && onNodeEvent) {
                onNodeEvent(parsed)
              }
              // 思考过程事件通过 onEvent 回调传递
              else if (parsed.type === 'thinking' && onEvent) {
                onEvent(parsed)
              }
            } else if (parsed.content) {
              // 兼容旧格式
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
      onError(error as Error)
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

// 上传并解析文件
export const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const token = await getValidAccessToken()

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
  create_time: string | null
  update_time: string | null
  is_pinned: boolean
  is_starred: boolean
  pinned_at: string | null
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

// 保存截断的AI消息
export const saveTruncatedMessage = (dialogId: string, content: string) => {
  return request.post('/chat/save-truncated', { dialog_id: dialogId, content })
}

// 批量删除对话消息
export const batchDeleteMessages = (dialogId: string, messageIds: string[]) => {
  return request.delete<{ dialog_id: string; deleted_count: number }>(`/dialog/${dialogId}/messages`, {
    params: { message_ids: messageIds },
    paramsSerializer: {
      serialize: (params: Record<string, any>) => {
        // 将 message_ids 数组序列化为多个同名参数: message_ids=a&message_ids=b
        const parts: string[] = []
        for (const key in params) {
          const value = params[key]
          if (Array.isArray(value)) {
            for (const v of value) {
              parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(v)}`)
            }
          } else {
            parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
          }
        }
        return parts.join('&')
      }
    }
  })
}

// 置顶/取消置顶对话
export const pinDialog = (dialogId: string, isPinned: boolean) => {
  return request.put(`/dialog/${dialogId}/pin`, { is_pinned: isPinned })
}

// 收藏/取消收藏对话
export const starDialog = (dialogId: string, isStarred: boolean) => {
  return request.put(`/dialog/${dialogId}/star`, { is_starred: isStarred })
}
