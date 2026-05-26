/** 聊天消息相关类型定义 */

// 思考过程步骤
export interface ThinkingStep {
  type: 'thinking'
  content?: string
}

// 工具调用事件
export interface ToolCallEvent {
  title: string        // 事件标题，如 "执行工具: 天气查询"
  status: 'START' | 'END' | 'ERROR'  // 事件状态
  message: string      // 事件详情（工具输入/输出）
  tool_name?: string   // 工具内部名称
  show?: boolean       // 前端展开/折叠状态
}

// 统一处理步骤（按到达顺序排列）
export interface ThinkingProcessStep {
  stepType: 'thinking'
  content?: string
}

export interface ToolProcessStep {
  stepType: 'tool'
  title: string
  status: 'START' | 'END' | 'ERROR'
  message: string
  tool_name?: string
  show?: boolean
}

export type ProcessStep = ThinkingProcessStep | ToolProcessStep

// 聊天消息
export interface Message {
  role: 'user' | 'ai'
  content: string
  time?: string
  processSteps?: ProcessStep[]      // 统一处理步骤（按顺序排列）
  thinkingSteps?: ThinkingStep[]    // 兼容旧数据
  eventInfo?: ToolCallEvent[]       // 兼容旧数据
  id?: string  // 消息ID（后端返回，用于批量删除）
}
