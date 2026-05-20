<template>
  <div class="chat-page">
    <!-- 工具栏 -->
    <div class="chat-toolbar">
      <div class="toolbar-left">
        <span class="page-title">智能对话</span>
      </div>
      <div class="toolbar-right">
        <el-button 
          size="default" 
          type="danger" 
          plain
          @click="clearChat"
          :disabled="messages.length <= 1"
        >
          <el-icon><Delete /></el-icon>
          清空对话
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
              accept=".txt,.md,.pdf,.docx,.html,.htm,.csv,.json"
            >
              <el-button size="default" :disabled="sending">
                <el-icon><Upload /></el-icon>
                上传文件
              </el-button>
            </el-upload>
            <span class="tip-text">支持: txt, md, pdf, docx, html, csv, json</span>
          </div>
          <div class="action-right">
            <span class="tip-text">按 Ctrl+Enter 发送</span>
            <el-button 
              type="primary" 
              @click="sendMessage"
              :loading="sending"
              :disabled="!inputMessage.trim()"
              class="send-button"
            >
              <el-icon v-if="!sending"><Promotion /></el-icon>
              {{ sending ? '发送中...' : '发送' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, Delete, User, Loading, Promotion, Service, SwitchButton, Document, Upload } from '@element-plus/icons-vue'
import { sendMessage as sendApiMessage, sendStreamMessage, uploadFile } from '../apis/chat'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// @ts-ignore
import MarkdownItClass from 'markdown-it'

const router = useRouter()

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

const messages = ref<Message[]>([
  { 
    role: 'ai', 
    content: '你好！我是 Hubu Agent，有什么可以帮助你的吗？',
    time: getCurrentTime()
  }
])
const inputMessage = ref('')
const sending = ref(false)
const sessionId = ref('session_' + Date.now())
const messagesRef = ref<HTMLElement>()
const currentAiMessageIndex = ref<number>(-1) // 当前正在生成的 AI 消息索引
const uploadedFile = ref<File | null>(null) // 上传的文件
const fileContent = ref<string>('') // 文件解析后的内容
const uploadingFile = ref(false) // 文件上传中

// 获取当前时间
function getCurrentTime(): string {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 格式化消息内容（支持Markdown和代码高亮）
function formatMessage(content: string): string {
  return md.render(content)
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 清空对话
const clearChat = () => {
  messages.value = [{ 
    role: 'ai', 
    content: '对话已清空，有什么可以帮助你的吗？',
    time: getCurrentTime()
  }]
  sessionId.value = 'session_' + Date.now()
  ElMessage.success('对话已清空')
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
  scrollToBottom()

  try {
    // 调用流式 API
    await sendStreamMessage(
      {
        message: userMessage,
        session_id: sessionId.value,
        file_content: fileContent.value || undefined  // 如果有文件内容则传递
      },
      // onChunk: 接收每个数据块
      (chunk: string) => {
        messages.value[aiMessageIndex].content += chunk
        scrollToBottom()
      },
      // onComplete: 完成回调
      () => {
        sending.value = false
        currentAiMessageIndex.value = -1
        // 清除已上传的文件
        clearFile()
        ElMessage.success('回复完成')
      },
      // onError: 错误回调
      (error: Error) => {
        ElMessage.error(error.message || '发送消息失败')
        console.error(error)
        // 移除失败的 AI 消息
        messages.value.splice(aiMessageIndex, 1)
        sending.value = false
        currentAiMessageIndex.value = -1
      }
    )
  } catch (error: any) {
    ElMessage.error(error.message || '发送消息失败')
    console.error(error)
    // 移除失败的消息
    messages.value.splice(aiMessageIndex - 1, 2) // 移除用户消息和 AI 消息
    sending.value = false
    currentAiMessageIndex.value = -1
  }
}

// 处理文件选择
async function handleFileChange(uploadFileItem: any) {
  if (!uploadFileItem.raw) return
  
  uploadingFile.value = true
  uploadedFile.value = uploadFileItem.raw
  
  try {
    // 上传并解析文件
    const result = await uploadFile(uploadFileItem.raw)
    fileContent.value = result.content
    
    ElMessage.success(`文件 "${uploadFileItem.name}" 上传成功`)
    
    // 可以在输入框中自动添加提示
    if (!inputMessage.value.trim()) {
      inputMessage.value = `请帮我分析这个文件的内容：`
    }
  } catch (error: any) {
    ElMessage.error(error.message || '文件上传失败')
    console.error(error)
    // 清除文件
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

// 组件挂载时滚动到底部
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
  gap: 12px;
}

.message-header strong {
  font-size: 14px;
  font-weight: 600;
}

.time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.message.user .time {
  color: rgba(255, 255, 255, 0.8);
}

.message-text {
  line-height: 1.8;
  font-size: 15px;
  word-wrap: break-word;
}

.message.user .message-text {
  color: white;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  color: #909399;
  font-size: 14px;
  justify-content: center;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 底部输入区域 */
.chat-footer {
  padding: 20px 24px;
  background-color: white;
  border-top: 1px solid #e4e7ed;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
  font-size: 15px;
  line-height: 1.6;
}

.message-input :deep(.el-textarea__inner):focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
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

.file-preview {
  margin-bottom: 8px;
}

.file-upload {
  display: inline-block;
}

.tip-text {
  font-size: 13px;
  color: #909399;
}

.send-button {
  min-width: 100px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 滚动条样式 */
:deep(.el-scrollbar__bar) {
  opacity: 0.3;
  transition: opacity 0.3s;
}

:deep(.el-scrollbar__bar:hover) {
  opacity: 0.6;
}

/* Markdown样式 */
.message-text :deep(p) {
  margin: 0.5em 0;
}

.message-text :deep(p:first-child) {
  margin-top: 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(code) {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.message.user .message-text :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
}

.message-text :deep(pre) {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 1em 0;
}

.message-text :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 0.5em 0;
  padding-left: 2em;
}

.message-text :deep(li) {
  margin: 0.25em 0;
}

.message-text :deep(blockquote) {
  border-left: 4px solid #667eea;
  padding-left: 1em;
  margin: 1em 0;
  color: #606266;
}

.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 8px;
  text-align: left;
}

.message-text :deep(th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

.message-text :deep(a) {
  color: #667eea;
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

.message-text :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-messages {
    padding: 16px 12px;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .chat-header {
    padding: 0 16px;
  }
  
  .chat-footer {
    padding: 16px;
  }
}
</style>
