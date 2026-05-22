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
            </div>
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
          </div>
        </div>

        <!-- 加载指示器 -->
        <div v-if="sending" class="loading-indicator">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span>AI正在思考...</span>
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
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, User, Loading, Promotion, Service, SwitchButton, Document, Upload, CircleClose, Download, Plus } from '@element-plus/icons-vue'
import { sendStreamMessage, cancelStreamMessage, uploadFile, deleteDialog, getDialogHistory, getDialogDetail } from '../apis/chat'
import type { DialogInfo } from '../apis/chat'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// @ts-ignore
import MarkdownItClass from 'markdown-it'

const router = useRouter()
const route = useRoute()

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

interface Message {
  role: 'user' | 'ai'
  content: string
  time?: string
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

  // 先处理 markdown 图片语法 ![alt](/api/v1/report/download/xxx)，避免被 md.render 渲染成图片预览
  let processed = content.replace(
    /!\[[^\]]*\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      return `<div class="report-download-card" data-report-id="${reportId}">
        <div class="report-card-icon">${cardIcon}</div>
        <div class="report-card-info">
          <div class="report-card-title">${cardTitle}</div>
          <div class="report-card-desc">${cardDesc}</div>
        </div>
        <a class="report-card-btn" href="/api/v1/report/download/${reportId}?token=${encodeURIComponent(localStorage.getItem('access_token') || '')}" target="_blank">
          <el-icon><Download /></el-icon> 下载
        </a>
      </div>`
    }
  )

  // 再处理普通链接 [文字](/api/v1/report/download/xxx)
  processed = processed.replace(
    /\[(?:📄|📋|📁|📦|💾|🔗|📊|📈)?[^\]]*?下载链接[^\]]*?\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      return `<div class="report-download-card" data-report-id="${reportId}">
        <div class="report-card-icon">${cardIcon}</div>
        <div class="report-card-info">
          <div class="report-card-title">${cardTitle}</div>
          <div class="report-card-desc">${cardDesc}</div>
        </div>
        <a class="report-card-btn" href="/api/v1/report/download/${reportId}?token=${encodeURIComponent(localStorage.getItem('access_token') || '')}" target="_blank">
          <el-icon><Download /></el-icon> 下载
        </a>
      </div>`
    }
  )

  processed = processed.replace(
    /(?<!\[)\/api\/v1\/report\/download\/([a-zA-Z0-9]+)/g,
    (match, reportId) => {
      if (processed.includes(`data-report-id="${reportId}"`)) return match
      return `<div class="report-download-card" data-report-id="${reportId}">
        <div class="report-card-icon">${cardIcon}</div>
        <div class="report-card-info">
          <div class="report-card-title">${cardTitle}</div>
          <div class="report-card-desc">${cardDesc}</div>
        </div>
        <a class="report-card-btn" href="/api/v1/report/download/${reportId}?token=${encodeURIComponent(localStorage.getItem('access_token') || '')}" target="_blank">
          <el-icon><Download /></el-icon> 下载
        </a>
      </div>`
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
    time: getCurrentTime()
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
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 工具栏样式 */
.chat-toolbar {
  background-color: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  flex-shrink: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px 20px;
}

.messages-container {
  max-width: 900px;
  margin: 0 auto;
}

/* 消息样式 */
.message {
  margin-bottom: 24px;
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
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

.message-content {
  max-width: 70%;
  background-color: white;
  border-radius: 12px;
  padding: 14px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-header strong {
  font-size: 14px;
}

.message-header .time {
  font-size: 12px;
  opacity: 0.6;
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-text :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
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
}

.message-text :deep(th), .message-text :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.message-text :deep(th) {
  background-color: #f5f7fa;
}

.message.user .message-text :deep(table a) {
  color: white;
}

/* 报告下载卡片 */
.message-text :deep(.report-download-card) {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 8px;
  margin: 8px 0;
  border: 1px solid #e4e7ed;
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
  color: #303133;
}

.message-text :deep(.report-card-desc) {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.message-text :deep(.report-card-btn) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  border-radius: 6px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: opacity 0.2s;
}

.message-text :deep(.report-card-btn:hover) {
  opacity: 0.9;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  color: #909399;
  font-size: 14px;
}

/* 输入区域 */
.chat-footer {
  background-color: white;
  border-top: 1px solid #e4e7ed;
  padding: 16px 24px;
  flex-shrink: 0;
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.file-preview {
  margin-bottom: 8px;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 14px;
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
  color: #909399;
}

.send-button, .stop-button {
  min-width: 80px;
}
</style>
