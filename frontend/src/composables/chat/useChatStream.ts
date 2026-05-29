import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  sendStreamMessage,
  cancelStreamMessage,
  deleteDialog,
  getDialogHistory,
  getDialogDetail,
  batchDeleteMessages,
  saveTruncatedMessage,
} from '../../apis/chat'
import type { ThinkingEvent, NodeEvent, ToolCallEvent } from '../../apis/chat'
import type { Message } from '../../types/chat'
import { loadChartPreviews } from '../useMarkdown'

/**
 * 将后端错误信息转换为用户友好的提示
 */
function _getFriendlyErrorMsg(errorMsg: string): string {
  const msg = errorMsg.toLowerCase()
  if (msg.includes('rate_limit') || msg.includes('rate limit') || msg.includes('429') || msg.includes('too many requests')) {
    return '请求过于频繁，请稍后再试'
  }
  if (msg.includes('timeout') || msg.includes('timed out') || msg.includes('超时')) {
    return '请求超时，请稍后重试'
  }
  if (msg.includes('connection') || msg.includes('network') || msg.includes('网络') || msg.includes('econnrefused')) {
    return '网络连接失败，请检查网络后重试'
  }
  if (msg.includes('authentication') || msg.includes('api key') || msg.includes('unauthorized') || msg.includes('401') || msg.includes('invalid_api_key')) {
    return 'API 认证失败，请检查模型配置'
  }
  if (msg.includes('quota') || msg.includes('billing') || msg.includes('insufficient_quota') || msg.includes('402')) {
    return 'API 额度不足，请联系管理员'
  }
  if (msg.includes('model_not_found') || msg.includes('model not') || msg.includes('404')) {
    return '模型不可用，请检查模型配置'
  }
  if (msg.includes('context_length') || msg.includes('max_tokens') || msg.includes('token_limit') || msg.includes('too many tokens')) {
    return '输入内容过长，请缩短后重试'
  }
  if (msg.includes('overloaded') || msg.includes('503') || msg.includes('server_error') || msg.includes('500')) {
    return '服务暂时不可用，请稍后重试'
  }
  return 'AI 处理失败，请稍后重试'
}

/** 获取当前时间 */
function getCurrentTime(): string {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

/** 初始欢迎消息 */
function getWelcomeMessage(): Message {
  return {
    role: 'ai',
    content: '你好！我是 Hubu Agent，有什么可以帮助你的吗？',
    time: getCurrentTime(),
  }
}

export function useChatStream() {
  const router = useRouter()

  // 核心状态
  const messages = ref<Message[]>([getWelcomeMessage()])
  const inputMessage = ref('')
  const sending = ref(false)
  const dialogId = ref<string | null>(null)
  const currentDialogName = ref<string>('新对话')
  const messagesRef = ref<HTMLElement>()
  const currentAiMessageIndex = ref<number>(-1)
  const isGenerating = ref(false)
  const thinkingExpanded = ref<Record<number, boolean>>({})

  // 当前思考步骤（用于加载指示器）
  const currentThinkingStep = computed(() => {
    if (currentAiMessageIndex.value < 0) return ''
    const msg = messages.value[currentAiMessageIndex.value]
    if (!msg) return ''
    const steps = msg.processSteps
    if (steps && steps.length > 0) {
      const lastTool = [...steps].reverse().find(s => s.stepType === 'tool')
      if (lastTool && lastTool.stepType === 'tool') {
        if (lastTool.status === 'START') return `🔄 ${lastTool.title}...`
        if (lastTool.status === 'END') return `✅ ${lastTool.title}`
        if (lastTool.status === 'ERROR') return `❌ ${lastTool.title}`
      }
      const lastThink = [...steps].reverse().find(s => s.stepType === 'thinking')
      if (lastThink) return '💭 正在思考...'
    }
    return ''
  })

  // 切换思考过程展开/折叠
  function toggleThinking(index: number) {
    thinkingExpanded.value[index] = !thinkingExpanded.value[index]
  }

  // 滚动到底部
  function scrollToBottom() {
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      }
      if (!isGenerating.value) {
        loadChartPreviews()
      }
    })
  }

  // 开始新对话
  const startNewDialog = () => {
    router.push('/chat')
  }

  // 删除当前对话
  const clearChat = async () => {
    if (!dialogId.value) return

    try {
      await ElMessageBox.confirm('确定要删除该对话吗？删除后无法恢复。', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })

      await deleteDialog(dialogId.value)
      ElMessage.success('对话已删除')
      window.dispatchEvent(new CustomEvent('refresh-dialogs'))
      router.push('/chat')
    } catch {
      // 用户取消
    }
  }

  // 加载对话历史
  const loadDialogHistory = async (id: string) => {
    try {
      const result = await getDialogHistory(id)
      dialogId.value = id
      try {
        const detail = await getDialogDetail(id)
        currentDialogName.value = detail.name
      } catch {}

      messages.value = result.messages.map((m: any) => ({
        id: m.id,
        role: m.role === 'assistant' ? 'ai' : m.role,
        content: m.content,
        time: m.create_time ? new Date(m.create_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '',
      }))
      if (messages.value.length === 0) {
        messages.value = [getWelcomeMessage()]
      }
      scrollToBottom()
    } catch (error: any) {
      ElMessage.error('加载对话历史失败')
      console.error(error)
      router.push('/chat')
    }
  }

  // 合并后端消息id到现有消息，保留思考过程和工具调用步骤
  const _mergeMessageIds = async (id: string) => {
    try {
      const result = await getDialogHistory(id)
      const serverMessages = result.messages
      for (let i = 0; i < serverMessages.length && i < messages.value.length; i++) {
        if (serverMessages[i].id && !messages.value[i].id) {
          messages.value[i].id = serverMessages[i].id
        }
      }
    } catch (error) {
      console.error('合并消息id失败:', error)
    }
  }

  /**
   * 构建流式消息的回调函数集
   * 抽取公共逻辑，sendMessage 和 regenerateMessage 共用
   */
  function _buildStreamCallbacks(
    aiMessageIndex: number,
    userContent: string,
    options: {
      onNodeEvent: (event: NodeEvent) => void,
      onWorkflowDone: () => void,
      resetWorkflow: () => void,
      clearFile: () => void,
      isRegenerate?: boolean,
    }
  ) {
    return {
      onChunk: (chunk: string) => {
        messages.value[aiMessageIndex].content += chunk
      },
      onComplete: (returnedDialogId?: string) => {
        if (returnedDialogId && !dialogId.value) {
          dialogId.value = returnedDialogId
          currentDialogName.value = userContent.slice(0, 20) + (userContent.length > 20 ? '...' : '')
          window.dispatchEvent(new CustomEvent('refresh-dialogs'))
          router.replace(`/chat/${returnedDialogId}`)
        }
        sending.value = false
        isGenerating.value = false
        currentAiMessageIndex.value = -1
        if (!options.isRegenerate) {
          options.clearFile()
        }
        if (dialogId.value) {
          _mergeMessageIds(dialogId.value)
        }
        scrollToBottom()
      },
      onError: (error: Error) => {
        if (error.name === 'AbortError') {
          ElMessage.info('已停止生成')
          const msg = messages.value[aiMessageIndex]
          if (msg && !msg.content.trim()) {
            msg.content = '（生成已停止）'
          }
        } else {
          console.error(error)
          const msg = messages.value[aiMessageIndex]
          const friendlyMsg = _getFriendlyErrorMsg(error.message || (options.isRegenerate ? '重新生成失败' : '发送消息失败'))
          if (msg) {
            msg.content = msg.content
              ? msg.content + '\n\n---\n⚠️ ' + friendlyMsg
              : '⚠️ ' + friendlyMsg
          }
          ElMessage.error(friendlyMsg)
        }
        sending.value = false
        isGenerating.value = false
        currentAiMessageIndex.value = -1
        scrollToBottom()
      },
      onThinking: (event: ThinkingEvent) => {
        const msg = messages.value[aiMessageIndex]
        if (!msg.processSteps) msg.processSteps = []
        msg.processSteps.push({
          stepType: 'thinking',
          content: event.content,
        })
      },
      onNodeEvent: options.onNodeEvent,
      onToolEvent: (event: ToolCallEvent) => {
        const msg = messages.value[aiMessageIndex]
        if (!msg.processSteps) msg.processSteps = []
        const { title, status, message } = event.data

        if (status === 'START') {
          msg.processSteps.push({ stepType: 'tool', title, status: 'START', message, show: false })
        } else if (status === 'END' || status === 'ERROR') {
          const existing = msg.processSteps.find(e => e.stepType === 'tool' && e.title === title && e.status === 'START')
          if (existing && existing.stepType === 'tool') {
            existing.status = status
            existing.message = message
          } else {
            msg.processSteps.push({ stepType: 'tool', title, status, message, show: false })
          }
        }
      },
      onDialogInit: (initDialogId: string) => {
        if (!dialogId.value) {
          dialogId.value = initDialogId
          if (!options.isRegenerate) {
            currentDialogName.value = userContent.slice(0, 20) + (userContent.length > 20 ? '...' : '')
            window.dispatchEvent(new CustomEvent('refresh-dialogs'))
            router.replace(`/chat/${initDialogId}`)
          }
        }
      },
    }
  }

  // 发送消息
  const sendMessage = (
    fileContent: string | undefined,
    callbacks: {
      onNodeEvent: (event: NodeEvent) => void,
      resetWorkflow: () => void,
      clearFile: () => void,
    }
  ) => {
    if (!inputMessage.value.trim()) {
      ElMessage.warning('请输入消息')
      return
    }

    const userMessage = inputMessage.value.trim()

    // 添加用户消息
    messages.value.push({
      role: 'user',
      content: userMessage,
      time: getCurrentTime(),
    })

    // 添加一个空的 AI 消息用于流式更新
    const aiMessageIndex = messages.value.length
    messages.value.push({
      role: 'ai',
      content: '',
      time: getCurrentTime(),
      processSteps: [],
    })
    currentAiMessageIndex.value = aiMessageIndex

    inputMessage.value = ''
    sending.value = true
    isGenerating.value = true
    callbacks.resetWorkflow()
    scrollToBottom()

    const streamCallbacks = _buildStreamCallbacks(aiMessageIndex, userMessage, {
      onNodeEvent: callbacks.onNodeEvent,
      onWorkflowDone: () => {},
      resetWorkflow: callbacks.resetWorkflow,
      clearFile: callbacks.clearFile,
    })

    try {
      sendStreamMessage(
        {
          message: userMessage,
          dialog_id: dialogId.value || undefined,
          file_content: fileContent,
        },
        streamCallbacks.onChunk,
        streamCallbacks.onComplete,
        streamCallbacks.onError,
        streamCallbacks.onThinking,
        streamCallbacks.onNodeEvent,
        streamCallbacks.onToolEvent,
        streamCallbacks.onDialogInit,
      )
    } catch (error: any) {
      console.error(error)
      const friendlyMsg = _getFriendlyErrorMsg(error.message || '发送消息失败')
      const aiMsg = messages.value[aiMessageIndex]
      if (aiMsg && aiMsg.role === 'ai') {
        aiMsg.content = '⚠️ ' + friendlyMsg
      }
      ElMessage.error(friendlyMsg)
      sending.value = false
      isGenerating.value = false
      currentAiMessageIndex.value = -1
      scrollToBottom()
    }
  }

  // 停止生成
  function stopGeneration() {
    if (isGenerating.value) {
      cancelStreamMessage()
      sending.value = false
      isGenerating.value = false
      currentAiMessageIndex.value = -1
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'ai') {
        if (!lastMsg.content.trim()) {
          lastMsg.content = '（生成已停止）'
        }
        if (dialogId.value) {
          saveTruncatedMessage(dialogId.value, lastMsg.content).catch((e) => {
            console.error('保存截断消息失败:', e)
          })
        }
      }
    }
  }

  // 保存正在生成中的消息（页面卸载/路由离开时调用）
  function saveInProgressMessage() {
    if (!isGenerating.value) return
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'ai' && lastMsg.content.trim() && dialogId.value) {
      // 取消流式请求
      cancelStreamMessage()
      // 保存已接收的内容
      saveTruncatedMessage(dialogId.value, lastMsg.content).catch((e) => {
        console.error('保存中断消息失败:', e)
      })
      // 重置状态
      sending.value = false
      isGenerating.value = false
      currentAiMessageIndex.value = -1
    }
  }

  // 重新生成最后一条AI消息
  async function regenerateMessage(
    aiMessageIndex: number,
    callbacks: {
      onNodeEvent: (event: NodeEvent) => void,
      resetWorkflow: () => void,
    }
  ) {
    if (isGenerating.value || sending.value) return
    if (!dialogId.value) return

    const aiMsg = messages.value[aiMessageIndex]
    if (!aiMsg || aiMsg.role !== 'ai') return

    const prevMsg = messages.value[aiMessageIndex - 1]
    if (!prevMsg || prevMsg.role !== 'user') return

    // 删除后端的AI消息
    if (aiMsg.id) {
      try {
        await batchDeleteMessages(dialogId.value, [aiMsg.id])
      } catch (e: any) {
        ElMessage.error(e.message || '删除AI消息失败')
        return
      }
    }

    // 从前端移除AI消息
    messages.value.splice(aiMessageIndex, 1)

    const userContent = prevMsg.content
    const newAiMessageIndex = messages.value.length
    messages.value.push({
      role: 'ai',
      content: '',
      time: getCurrentTime(),
      processSteps: [],
    })
    currentAiMessageIndex.value = newAiMessageIndex

    sending.value = true
    isGenerating.value = true
    callbacks.resetWorkflow()
    scrollToBottom()

    const streamCallbacks = _buildStreamCallbacks(newAiMessageIndex, userContent, {
      onNodeEvent: callbacks.onNodeEvent,
      onWorkflowDone: () => {},
      resetWorkflow: callbacks.resetWorkflow,
      clearFile: () => {},
      isRegenerate: true,
    })

    try {
      sendStreamMessage(
        {
          message: userContent,
          dialog_id: dialogId.value,
        },
        streamCallbacks.onChunk,
        streamCallbacks.onComplete,
        streamCallbacks.onError,
        streamCallbacks.onThinking,
        streamCallbacks.onNodeEvent,
        streamCallbacks.onToolEvent,
        streamCallbacks.onDialogInit,
      )
    } catch (error: any) {
      console.error(error)
      const friendlyMsg = _getFriendlyErrorMsg(error.message || '重新生成失败')
      const aiMsg = messages.value[newAiMessageIndex]
      if (aiMsg && aiMsg.role === 'ai') {
        aiMsg.content = '⚠️ ' + friendlyMsg
      }
      ElMessage.error(friendlyMsg)
      sending.value = false
      isGenerating.value = false
      currentAiMessageIndex.value = -1
      scrollToBottom()
    }
  }

  // 退出登录
  function handleLogout() {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      localStorage.removeItem('access_token')
      ElMessage.success('已退出登录')
      router.push('/login')
    }).catch(() => {})
  }

  return {
    // 状态
    messages,
    inputMessage,
    sending,
    dialogId,
    currentDialogName,
    messagesRef,
    currentAiMessageIndex,
    isGenerating,
    thinkingExpanded,
    currentThinkingStep,
    // 方法
    getWelcomeMessage,
    toggleThinking,
    scrollToBottom,
    startNewDialog,
    clearChat,
    loadDialogHistory,
    sendMessage,
    stopGeneration,
    saveInProgressMessage,
    regenerateMessage,
    handleLogout,
  }
}
