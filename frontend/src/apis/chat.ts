import request from './request'
import { fetchWithTokenRefresh, getAccessToken } from './auth'

export interface ChatMessage {
  message: string
  session_id?: string
  file_content?: string  // 文件解析后的内容
}

export interface ChatResponse {
  response: string
  session_id: string
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
  onComplete: () => void,
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
export const getChatHistory = (sessionId: string) => {
  return request.get(`/chat/history/${sessionId}`)
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
