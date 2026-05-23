<template>
  <div class="chat-page">
    <!-- 工具栏 -->
    <div class="chat-toolbar">
      <div class="toolbar-left">
        <span class="page-title">{{ currentDialogName }}</span>
      </div>
      <div class="toolbar-right">
        <el-button
          size="default"
          type="primary"
          plain
          @click="startNewDialog"
        >
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
        <el-button
          size="default"
          type="danger"
          plain
          @click="clearChat"
          :disabled="!dialogId"
        >
          <el-icon><Delete /></el-icon>
          删除对话
        </el-button>
        <el-button
          size="default"
          type="info"
          plain
          @click="handleLogout"
        >
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </div>

    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesRef">
      <div class="messages-container">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message', msg.role]"
        >
          <div class="avatar">
            <el-avatar :size="40" v-if="msg.role === 'user'">
              <el-icon :size="24"><User /></el-icon>
            </el-avatar>
            <el-avatar :size="40" v-else>
              <el-icon :size="24"><Service /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-header">
              <strong>{{ msg.role === 'user' ? '你' : 'AI助手' }}</strong>
              <span class="time">{{ msg.time }}</span>
              <!-- 思考过程折叠按钮 -->
              <el-button
                v-if="msg.thinkingSteps && msg.thinkingSteps.length > 0"
                size="small"
                text
                class="thinking-toggle"
                @click="toggleThinking(index)"
              >
                <el-icon><View /></el-icon>
                {{ thinkingExpanded[index] ? '隐藏思考过程' : '查看思考过程' }}
              </el-button>
            </div>
            <!-- 思考过程展示区域 -->
            <div v-if="msg.thinkingSteps && msg.thinkingSteps.length > 0 && thinkingExpanded[index]" class="thinking-steps">
              <div
                v-for="(step, sIdx) in msg.thinkingSteps"
                :key="sIdx"
                :class="['thinking-step', step.type]"
              >
                <div class="step-header">
                  <span class="step-icon">
                    <template v-if="step.type === 'thinking'">💭</template>
                    <template v-else-if="step.type === 'tool_start'">🔧</template>
                    <template v-else-if="step.type === 'tool_end'">✅</template>
                  </span>
                  <span class="step-label">
                    <template v-if="step.type === 'thinking'">思考</template>
                    <template v-else-if="step.type === 'tool_start'">调用工具: {{ formatToolName(step.tool || '') }}</template>
                    <template v-else-if="step.type === 'tool_end'">工具结果: {{ formatToolName(step.tool || '') }}</template>
                  </span>
                </div>
                <div class="step-content" v-if="step.type === 'thinking' && step.content">
                  {{ step.content }}
                </div>
                <div class="step-content" v-else-if="step.type === 'tool_start' && step.input">
                  <pre>{{ formatToolInput(step.input) }}</pre>
                </div>
                <div class="step-content" v-else-if="step.type === 'tool_end' && step.output">
                  <pre>{{ step.output }}</pre>
                </div>
              </div>
            </div>
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
          </div>
        </div>

        <!-- 加载指示器 -->
        <div v-if="sending" class="loading-indicator">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span v-if="currentThinkingStep">{{ currentThinkingStep }}</span>
          <span v-else>AI正在思考...</span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-footer">
      <div class="input-wrapper">
        <!-- 文件预览 -->
        <div v-if="uploadedFile" class="file-preview">
          <el-tag closable @close="clearFile" type="info">
            <el-icon><Document /></el-icon>
            {{ uploadedFile.name }}
          </el-tag>
        </div>

        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息... (Ctrl+Enter 发送)"
          @keyup.ctrl.enter="sendMessage"
          :disabled="sending"
          resize="none"
          class="message-input"
        />
        <div class="input-actions">
          <div class="action-left">
            <el-upload
              class="file-upload"
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
              accept=".txt,.md,.pdf,.docx,.html,.htm,.csv,.json,.xml,.xlsx,.pptx,.rtf"
            >
              <el-button size="default" :disabled="sending">
                <el-icon><Upload /></el-icon>
                上传文件
              </el-button>
            </el-upload>
            <span class="tip-text">支持: txt, md, pdf, docx, html, csv, json, xml, xlsx, pptx, rtf</span>
          </div>
          <div class="action-right">
            <span class="tip-text">按 Ctrl+Enter 发送</span>
            <el-button
              v-if="!isGenerating"
              type="primary"
              @click="sendMessage"
              :loading="sending"
              :disabled="!inputMessage.trim()"
              class="send-button"
            >
              <el-icon v-if="!sending"><Promotion /></el-icon>
              {{ sending ? '发送中...' : '发送' }}
            </el-button>
            <el-button
              v-else
              type="danger"
              @click="stopGeneration"
              class="stop-button"
            >
              <el-icon><CircleClose /></el-icon>
              停止生成
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, User, Loading, Promotion, Service, SwitchButton, Document, Upload, CircleClose, Download, Plus, View } from '@element-plus/icons-vue'
import { sendStreamMessage, cancelStreamMessage, uploadFile, deleteDialog, getDialogHistory, getDialogDetail } from '../apis/chat'
import type { DialogInfo, ThinkingEvent } from '../apis/chat'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// @ts-ignore
import MarkdownItClass from 'markdown-it'

const router = useRouter()
const route = useRoute()

// 全局图片预览函数（点击图片弹出全屏查看）
;(window as any).__previewImage = (blobUrl: string) => {
  const overlay = document.createElement('div')
  overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:9999;cursor:zoom-out;'
  const img = document.createElement('img')
  img.src = blobUrl
  img.style.cssText = 'max-width:90vw;max-height:90vh;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4);'
  overlay.appendChild(img)
  overlay.addEventListener('click', () => {
    document.body.removeChild(overlay)
  })
  document.body.appendChild(overlay)
}

// 全局下载函数（供 v-html 中的 onclick 调用）
;(window as any).__downloadFile = (reportId: string) => {
  const token = localStorage.getItem('access_token') || ''
  const url = `/api/v1/report/download/${reportId}?token=${encodeURIComponent(token)}`
  window.open(url, '_blank')
}

// 异步加载图表预览图片（用 fetch + blob 避免 token 认证问题）
function loadChartPreviews() {
  const previews = document.querySelectorAll('.report-card-preview[data-report-id]')
  previews.forEach((el) => {
    const reportId = (el as HTMLElement).dataset.reportId
    if (!reportId || (el as HTMLElement).dataset.loaded) return
    ;(el as HTMLElement).dataset.loaded = 'true'
    const token = localStorage.getItem('access_token') || ''
    fetch(`/api/v1/report/download/${reportId}?token=${encodeURIComponent(token)}`)
      .then(res => {
        if (!res.ok) throw new Error('加载失败')
        return res.blob()
      })
      .then(blob => {
        const blobUrl = URL.createObjectURL(blob)
        el.innerHTML = `<img src="${blobUrl}" alt="图表预览" onclick="window.__previewImage('${blobUrl}')" />`
      })
      .catch(() => {
        el.innerHTML = '<div class="report-card-preview-error">预览加载失败</div>'
      })
  })
}

// Markdown解析器配置
// @ts-ignore
const md = new MarkdownItClass({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code>' +
               hljs.highlight(str, { language: lang }).value +
               '</code></pre>'
      } catch (__) {}
    }
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

interface ThinkingStep {
  type: 'thinking' | 'tool_start' | 'tool_end'
  content?: string
  tool?: string
  input?: string
  output?: string
}

interface Message {
  role: 'user' | 'ai'
  content: string
  time?: string
  thinkingSteps?: ThinkingStep[]
}

// 初始欢迎消息
function getWelcomeMessage(): Message {
  return {
    role: 'ai',
    content: '你好！我是 Hubu Agent，有什么可以帮助你的吗？',
    time: getCurrentTime()
  }
}

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

// 切换思考过程展开/折叠
function toggleThinking(index: number) {
  thinkingExpanded.value[index] = !thinkingExpanded.value[index]
}

// 格式化工具名称
function formatToolName(toolName: string): string {
  const nameMap: Record<string, string> = {
    'web_search': '网络搜索',
    'knowledge_search': '知识库搜索',
    'calculator': '计算器',
    'code_runner': '代码执行',
    'chart_generator': '图表生成',
    'report_generator': '报告生成',
    'web_scraper': '网页抓取',
    'memory_search': '记忆搜索'
  }
  return nameMap[toolName] || toolName
}

// 格式化工具输入（截断过长内容）
function formatToolInput(input: string): string {
  try {
    const parsed = JSON.parse(input)
    const formatted = JSON.stringify(parsed, null, 2)
    return formatted.length > 300 ? formatted.slice(0, 300) + '...' : formatted
  } catch {
    return input.length > 300 ? input.slice(0, 300) + '...' : input
  }
}

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

// 格式化消息内容（支持Markdown和代码高亮）
function formatMessage(content: string): string {
  const isChart = content.includes('📊') || content.includes('图表生成成功')
  const cardIcon = isChart ? '📊' : '📄'
  const cardTitle = isChart ? '图表文件已生成' : '报告文件已生成'
  const cardDesc = isChart ? '点击右侧按钮下载图表' : '点击右侧按钮下载报告'

  // 生成下载卡片（图表类型只显示预览，报告类型显示下载卡片）
  function makeDownloadCard(reportId: string): string {
    if (isChart) {
      return `<div class="report-card-preview" data-report-id="${reportId}">
        <div class="report-card-preview-loading">加载中...</div>
      </div>`
    }
    return `<div class="report-download-card" data-report-id="${reportId}">
      <div class="report-card-icon">${cardIcon}</div>
      <div class="report-card-info">
        <div class="report-card-title">${cardTitle}</div>
        <div class="report-card-desc">${cardDesc}</div>
      </div>
      <button class="report-card-btn" onclick="window.__downloadFile('${reportId}')">下载</button>
    </div>`
  }

  // 用 Set 记录已处理的 reportId，避免重复生成卡片
  const processedIds = new Set<string>()

  // 1. 处理 markdown 图片语法 ![alt](/api/v1/report/download/xxx)，避免被 md.render 渲染成图片预览
  let processed = content.replace(
    /!\[[^\]]*\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  // 2. 处理普通链接 [文字](/api/v1/report/download/xxx)
  processed = processed.replace(
    /\[[^\]]*\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  // 3. 处理纯文本下载链接（如 "🔗 下载链接: /api/v1/report/download/xxx"）
  processed = processed.replace(
    /(?:🔗\s*)?下载链接[：:]\s*\/api\/v1\/report\/download\/([a-zA-Z0-9]+)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  // 4. 处理裸链接 /api/v1/report/download/xxx
  processed = processed.replace(
    /(?<!\(|\[)\/api\/v1\/report\/download\/([a-zA-Z0-9]+)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  return md.render(processed)
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
    loadChartPreviews()
  })
}

// 开始新对话 - 跳转到新对话路由
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
    // 通知 App.vue 刷新列表
    window.dispatchEvent(new CustomEvent('refresh-dialogs'))
    // 跳转到新对话
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
    // 获取对话详情（名称）
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
    // 加载失败则跳转到新对话
    router.push('/chat')
  }
}

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
  scrollToBottom()

  try {
    // 调用流式 API
    await sendStreamMessage(
      {
        message: userMessage,
        dialog_id: dialogId.value || undefined,
        file_content: fileContent.value || undefined
      },
      // onChunk: 接收每个数据块
      (chunk: string) => {
        messages.value[aiMessageIndex].content += chunk
        scrollToBottom()
      },
      // onComplete: 完成回调，可能包含 dialog_id
      (returnedDialogId?: string) => {
        // 如果是新对话，保存返回的 dialog_id 并跳转
        if (returnedDialogId && !dialogId.value) {
          dialogId.value = returnedDialogId
          currentDialogName.value = userMessage.slice(0, 20) + (userMessage.length > 20 ? '...' : '')
          // 通知 App.vue 刷新对话列表
          window.dispatchEvent(new CustomEvent('refresh-dialogs'))
          // 跳转到该对话的路由（替换当前历史记录，避免回退到空白新对话页）
          router.replace(`/chat/${returnedDialogId}`)
        }
        sending.value = false
        isGenerating.value = false
        currentAiMessageIndex.value = -1
        clearFile()
      },
      // onError: 错误回调
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
      // onEvent: 接收思考过程事件
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
        scrollToBottom()
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
      inputMessage.value = `请帮我分析这个文件的内容：`
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

// 监听路由参数变化，加载对话历史
watch(
  () => route.params.dialogId,
  (newDialogId) => {
    if (newDialogId) {
      const id = newDialogId as string
      if (id !== dialogId.value) {
        loadDialogHistory(id)
      }
    } else {
      // 新对话页面
      dialogId.value = null
      currentDialogName.value = '新对话'
      messages.value = [getWelcomeMessage()]
      clearFile()
    }
  },
  { immediate: true }
)

// 组件挂载时
onMounted(() => {
  scrollToBottom()
})

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
  }).catch(() => {
    // 用户取消
  })
}

// 暴露方法给父组件（侧边栏对话列表切换用）
defineExpose({
  dialogId,
  loadDialogHistory,
  startNewDialog
})
</script>

<style scoped>
.chat-page {
  height: 100%;
  width: 100%;
  background-color: #f0f2f5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 工具栏样式 */
.chat-toolbar {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  flex-shrink: 0;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 28px 24px;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 6px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

.messages-container {
  max-width: 860px;
  margin: 0 auto;
}

/* 消息样式 */
.message {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
}

.message.user .avatar :deep(.el-avatar) {
  background: #09b572;
}

.message.ai .avatar :deep(.el-avatar) {
  background: #4b5563;
}

.message-content {
  max-width: 72%;
  background-color: white;
  border-radius: 16px;
  padding: 14px 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease;
}

.message-content:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.message.user .message-content {
  background: #09b572;
  color: white;
  border-radius: 16px 16px 4px 16px;
}

.message.ai .message-content {
  border-radius: 16px 16px 16px 4px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-header strong {
  font-size: 13px;
  font-weight: 600;
}

.message.user .message-header strong {
  color: rgba(255, 255, 255, 0.9);
}

.message.ai .message-header strong {
  color: #374151;
}

.message-header .time {
  font-size: 11px;
  opacity: 0.5;
}

.message-text {
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.message-text :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 16px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 8px 0;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.message-text :deep(code) {
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.message-text :deep(:not(pre) > code) {
  background: rgba(9, 181, 114, 0.08);
  color: #09b572;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message.user .message-text :deep(:not(pre) > code) {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
}

.message-text :deep(p) {
  margin: 4px 0;
}

.message-text :deep(ul), .message-text :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  border-radius: 8px;
  overflow: hidden;
}

.message-text :deep(th), .message-text :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

.message-text :deep(th) {
  background-color: #f3f4f6;
  font-weight: 600;
  color: #374151;
}

.message-text :deep(td) {
  color: #4b5563;
}

.message.user .message-text :deep(th) {
  background-color: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.9);
}

.message.user .message-text :deep(td) {
  color: rgba(255, 255, 255, 0.85);
  border-color: rgba(255, 255, 255, 0.15);
}

.message.user .message-text :deep(table a) {
  color: white;
}

/* 图表预览区域 */
.message-text :deep(.report-card-preview) {
  margin: 8px 0 4px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}
.message-text :deep(.report-card-preview:hover) {
  box-shadow: 0 4px 16px rgba(9, 181, 114, 0.2);
  border-color: rgba(9, 181, 114, 0.3);
}
.message-text :deep(.report-card-preview img) {
  display: block;
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  background: #fafbfc;
  cursor: pointer;
}
.message-text :deep(.report-card-preview-loading) {
  padding: 28px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  background: #fafbfc;
}
.message-text :deep(.report-card-preview-error) {
  padding: 16px;
  text-align: center;
  color: #ef4444;
  font-size: 13px;
  background: #fef2f2;
}

/* 报告下载卡片 */
.message-text :deep(.report-download-card) {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #fafbfc 0%, #f3f4f6 100%);
  border-radius: 12px;
  margin: 8px 0;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.message-text :deep(.report-download-card:hover) {
  border-color: rgba(9, 181, 114, 0.3);
  box-shadow: 0 2px 8px rgba(9, 181, 114, 0.1);
}

.message-text :deep(.report-card-icon) {
  font-size: 28px;
}

.message-text :deep(.report-card-info) {
  flex: 1;
}

.message-text :deep(.report-card-title) {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.message-text :deep(.report-card-desc) {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}

.message-text :deep(.report-card-btn) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 20px;
  background: #09b572;
  color: white !important;
  border-radius: 8px;
  border: none;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.message-text :deep(.report-card-btn:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(9, 181, 114, 0.35);
}

/* 思考过程样式 */
.thinking-toggle {
  margin-left: 8px;
  font-size: 12px;
  color: #9ca3af !important;
}

.thinking-toggle:hover {
  color: #09b572 !important;
}

.thinking-steps {
  background: #fafbfc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.thinking-steps::-webkit-scrollbar {
  width: 4px;
}

.thinking-steps::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.thinking-step {
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.thinking-step:last-child {
  margin-bottom: 0;
}

.thinking-step.thinking {
  background: rgba(9, 181, 114, 0.06);
  border-left: 3px solid #09b572;
}

.thinking-step.tool_start {
  background: rgba(245, 158, 11, 0.06);
  border-left: 3px solid #f59e0b;
}

.thinking-step.tool_end {
  background: rgba(16, 185, 129, 0.06);
  border-left: 3px solid #10b981;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.step-icon {
  font-size: 14px;
}

.step-label {
  font-weight: 500;
  color: #374151;
}

.step-content {
  color: #6b7280;
  font-size: 12px;
  padding-left: 22px;
}

.step-content pre {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 8px 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 4px 0;
  font-size: 12px;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  color: #9ca3af;
  font-size: 14px;
}

.loading-indicator .is-loading {
  color: #09b572;
}

/* 输入区域 */
.chat-footer {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding: 16px 28px;
  flex-shrink: 0;
}

.input-wrapper {
  max-width: 860px;
  margin: 0 auto;
}

.file-preview {
  margin-bottom: 8px;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  font-size: 14px;
  border-color: #e5e7eb;
  transition: all 0.2s;
}

.message-input :deep(.el-textarea__inner:focus) {
  border-color: #09b572;
  box-shadow: 0 0 0 3px rgba(9, 181, 114, 0.1);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.action-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tip-text {
  font-size: 12px;
  color: #9ca3af;
}

.send-button, .stop-button {
  min-width: 80px;
}
</style>
