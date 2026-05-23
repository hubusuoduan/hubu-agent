/** 聊天消息相关类型定义 */

// 思考过程步骤
export interface ThinkingStep {
  type: 'thinking' | 'tool_start' | 'tool_end'
  content?: string
  tool?: string
  input?: string
  output?: string
}

// 聊天消息
export interface Message {
  role: 'user' | 'ai'
  content: string
  time?: string
  thinkingSteps?: ThinkingStep[]
}
