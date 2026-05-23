import { ref, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { sendStreamMessage, cancelStreamMessage, uploadFile, deleteDialog, getDialogHistory, getDialogDetail } from '../apis/chat'
import type { DialogInfo, ThinkingEvent, NodeEvent } from '../apis/chat'
import type { NodeTraceInfo } from '../components/WorkflowGraph.vue'
import type { Message } from '../types/chat'
import { loadChartPreviews, formatToolName } from './useMarkdown'

export function useChat() {
  const router = useRouter()
  const route = useRoute()

  // 消息列表
  const messages = ref<Message[]>([getWelcomeMessage()])
  const inputMessage = ref('')
  const sending = ref(false)
  const dialogId = ref<string | null>(null)
  const currentDialogName = ref<string>('新对话')
  const messagesRef = ref<HTMLElement>()
  const currentAiMessageIndex = ref<number>(-1)
  const uploadedFile = ref<File | null>(null)
  const fileContent = ref<string>('')
  const uploadingFile = ref(false)
  const isGenerating = ref(false)
  const thinkingExpanded = ref<Record<number, boolean>>({})

  // 工作流可视化面板
  const showWorkflowPanel = ref(false)
  const nodeTraces = ref<Record<string, NodeTraceInfo>>({})
  const workflowTotalMs = ref<number>(0)

  // 当前思考步骤（用于加载指示器）
  const currentThinkingStep = computed(() => {
    if (currentAiMessageIndex.value < 0) return ''
    const msg = messages.value[currentAiMessageIndex.value]
    if (!msg || !msg.thinkingSteps || msg.thinkingSteps.length === 0) return ''
    const lastStep = msg.thinkingSteps[msg.thinkingSteps.length - 1]
    if (lastStep.type === 'thinking') return '💭 正在思考...'
    if (lastStep.type === 'tool_start') return `🔧 正在调用${formatToolName(lastStep.tool || '工具')}...`
    if (lastStep.type === 'tool_end') return `✅ ${formatToolName(lastStep.tool || '工具')}执行完成`
    return 'AI正在思考...'
  })

  // 获取当前时间
  function getCurrentTime(): string {
    const now = new Date()
    return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  // 初始欢迎消息
  function getWelcomeMessage(): Message {
    return {
      role: 'ai',
      content: '你好！我是 Hubu Agent，有什么可以帮助你的吗？',
      time: getCurrentTime()
    }
  }

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
      // 只在非生成状态时加载图表预览，避免流式过程中 DOM 反复重渲染导致竞争
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
        type: 'warning'
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
        role: m.role === 'assistant' ? 'ai' : m.role,
        content: m.content,
        time: m.create_time ? new Date(m.create_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''
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

  // 发送消息
  const sendMessage = async () => {
    if (!inputMessage.value.trim()) {
      ElMessage.warning('请输入消息')
      return
    }

    const userMessage = inputMessage.value.trim()

    // 添加用户消息
    messages.value.push({
      role: 'user',
      content: userMessage,
      time: getCurrentTime()
    })

    // 添加一个空的 AI 消息用于流式更新
    const aiMessageIndex = messages.value.length
    messages.value.push({
      role: 'ai',
      content: '',
      time: getCurrentTime(),
      thinkingSteps: []
    })
    currentAiMessageIndex.value = aiMessageIndex

    inputMessage.value = ''
    sending.value = true
    isGenerating.value = true
    // 重置节点追踪状态
    nodeTraces.value = {}
    workflowTotalMs.value = 0
    scrollToBottom()

    try {
      await sendStreamMessage(
        {
          message: userMessage,
          dialog_id: dialogId.value || undefined,
          file_content: fileContent.value || undefined
        },
        // onChunk
        (chunk: string) => {
          messages.value[aiMessageIndex].content += chunk
        },
        // onComplete
        (returnedDialogId?: string) => {
          if (returnedDialogId && !dialogId.value) {
            dialogId.value = returnedDialogId
            currentDialogName.value = userMessage.slice(0, 20) + (userMessage.length > 20 ? '...' : '')
            window.dispatchEvent(new CustomEvent('refresh-dialogs'))
            router.replace(`/chat/${returnedDialogId}`)
          }
          sending.value = false
          isGenerating.value = false
          currentAiMessageIndex.value = -1
          clearFile()
          // 流式完成后滚动到底部并加载图表预览
          scrollToBottom()
        },
        // onError
        (error: Error) => {
          if (error.name === 'AbortError') {
            ElMessage.info('已停止生成')
          } else {
            ElMessage.error(error.message || '发送消息失败')
            console.error(error)
            messages.value.splice(aiMessageIndex, 1)
          }
          sending.value = false
          isGenerating.value = false
          currentAiMessageIndex.value = -1
        },
        // onEvent: 思考过程事件
        (event: ThinkingEvent) => {
          const msg = messages.value[aiMessageIndex]
          if (msg.thinkingSteps) {
            msg.thinkingSteps.push({
              type: event.type,
              content: event.content,
              tool: event.tool,
              input: event.input,
              output: event.output
            })
          }
        },
        // onNodeEvent: 节点追踪事件
        (event: NodeEvent) => {
          if (event.type === 'node_start' && event.node) {
            nodeTraces.value[event.node] = {
              node: event.node,
              display_name: event.display_name || event.node,
              status: 'running',
            }
            if (!showWorkflowPanel.value) {
              showWorkflowPanel.value = true
            }
          } else if (event.type === 'node_end' && event.node) {
            nodeTraces.value[event.node] = {
              node: event.node,
              display_name: event.display_name || event.node,
              status: 'completed',
              duration_ms: event.duration_ms,
              input_summary: event.input_summary,
              output_summary: event.output_summary,
            }
          } else if (event.type === 'node_error' && event.node) {
            nodeTraces.value[event.node] = {
              node: event.node,
              display_name: event.display_name || event.node,
              status: 'error',
              error: event.error,
            }
          } else if (event.type === 'workflow_done') {
            workflowTotalMs.value = event.total_duration_ms || 0
          }
        }
      )
    } catch (error: any) {
      ElMessage.error(error.message || '发送消息失败')
      console.error(error)
      messages.value.splice(aiMessageIndex - 1, 2)
      sending.value = false
      isGenerating.value = false
      currentAiMessageIndex.value = -1
    }
  }

  // 停止生成
  function stopGeneration() {
    if (isGenerating.value) {
      cancelStreamMessage()
      sending.value = false
      isGenerating.value = false
      currentAiMessageIndex.value = -1
    }
  }

  // 处理文件选择
  async function handleFileChange(uploadFileItem: any) {
    if (!uploadFileItem.raw) return

    const allowedExtensions = ['.txt', '.md', '.pdf', '.docx', '.html', '.htm', '.csv', '.json', '.xml', '.xlsx', '.pptx', '.rtf']
    const fileExt = '.' + uploadFileItem.name.split('.').pop().toLowerCase()

    if (!allowedExtensions.includes(fileExt)) {
      ElMessage.error(`不支持的文件类型: ${fileExt}。支持: ${allowedExtensions.join(', ')}`)
      return
    }

    uploadingFile.value = true
    uploadedFile.value = uploadFileItem.raw

    try {
      const result = await uploadFile(uploadFileItem.raw)
      fileContent.value = result.content
      ElMessage.success(`文件 "${uploadFileItem.name}" 上传成功`)

      if (!inputMessage.value.trim()) {
        inputMessage.value = '请帮我分析这个文件的内容：'
      }
    } catch (error: any) {
      ElMessage.error(error.message || '文件上传失败')
      console.error(error)
      clearFile()
    } finally {
      uploadingFile.value = false
    }
  }

  // 清除已上传的文件
  function clearFile() {
    uploadedFile.value = null
    fileContent.value = ''
  }

  // 退出登录
  function handleLogout() {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
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
    uploadedFile,
    fileContent,
    uploadingFile,
    isGenerating,
    thinkingExpanded,
    showWorkflowPanel,
    nodeTraces,
    workflowTotalMs,
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
    handleFileChange,
    clearFile,
    handleLogout,
  }
}
