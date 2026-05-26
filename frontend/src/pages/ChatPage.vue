<template>
  <div class="chat-page">
    <!-- 工具栏 -->
    <div class="chat-toolbar">
      <div class="toolbar-left">
        <el-button
          circle
          :disabled="!dialogId"
          @click="showExportDialog = true"
          class="toolbar-icon-btn"
        >
          <el-icon><Download /></el-icon>
        </el-button>
        <el-button
          circle
          @click="handleLogout"
          class="toolbar-icon-btn"
        >
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
      <div class="toolbar-center">
        <span v-if="dialogId" class="dialog-title">{{ currentDialogName }}</span>
      </div>
      <div class="toolbar-right"></div>
    </div>

    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesRef">
      <div class="messages-container">
        <ChatMessage
          v-for="(msg, index) in messages"
          :key="index"
          :msg="msg"
          :index="index"
          :expanded="!!thinkingExpanded[index]"
          :is-delete-mode="isDeleteMode"
          :is-selected="!!msg.id && selectedMessageIds.has(msg.id)"
          :is-last-ai-message="isLastAiMessage(index)"
          :has-prev-user-message="index > 0 && messages[index - 1].role === 'user'"
          @toggle-thinking="toggleThinking"
          @toggle-select="toggleMessageSelection"
          @regenerate="regenerateMessage"
          @enter-delete-mode="enterDeleteMode"
        />

        <!-- 加载指示器 -->
        <div v-if="sending" class="loading-indicator">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span v-if="currentThinkingStep">{{ currentThinkingStep }}</span>
          <span v-else>AI正在思考...</span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <ChatInput
      v-model:input-message="inputMessage"
      :sending="sending"
      :is-generating="isGenerating"
      :uploaded-files="uploadedFiles"
      :model-list="modelList"
      :current-model-id="currentModelId"
      :is-delete-mode="isDeleteMode"
      :selected-count="selectedMessageIds.size"
      @send-message="sendMessage"
      @stop-generation="stopGeneration"
      @clear-file="clearFile"
      @remove-file="removeFile"
      @file-change="handleFileChange"
      @switch-model="handleSwitchModel"
      @confirm-delete="confirmBatchDelete"
      @cancel-delete="exitDeleteMode"
      @select-all="toggleSelectAll"
    />

    <!-- 工作流可视化侧边栏（覆盖在右侧） -->
    <WorkflowSidebar
      :visible="showWorkflowPanel"
      :node-traces="nodeTraces"
      :total-duration-ms="workflowTotalMs"
      @close="showWorkflowPanel = false"
      @open="showWorkflowPanel = true"
    />

    <!-- 导出对话框 -->
    <ExportDialog
      v-model="showExportDialog"
      :dialog-id="dialogId"
      :message-count="messages.length"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Delete, Loading, SwitchButton, Plus, Download } from '@element-plus/icons-vue'
import ChatMessage from '../components/ChatMessage.vue'
import ChatInput from '../components/ChatInput.vue'
import WorkflowSidebar from '../components/WorkflowSidebar.vue'
import ExportDialog from '../components/ExportDialog.vue'
import { useChat } from '../composables/useChat'
import { initPreviewImage, initDownloadFile } from '../composables/useMarkdown'

// 初始化全局函数（供 v-html 中的 onclick 调用）
initPreviewImage()
initDownloadFile()

const route = useRoute()

// 从 composable 获取所有聊天逻辑
const {
  messages,
  inputMessage,
  sending,
  dialogId,
  currentDialogName,
  messagesRef,
  uploadedFiles,
  uploadingFile,
  isGenerating,
  thinkingExpanded,
  isDeleteMode,
  selectedMessageIds,
  showWorkflowPanel,
  nodeTraces,
  workflowTotalMs,
  currentThinkingStep,
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
  removeFile,
  handleLogout,
  enterDeleteMode,
  exitDeleteMode,
  toggleMessageSelection,
  toggleSelectAll,
  confirmBatchDelete,
  regenerateMessage,
  modelList,
  currentModelId,
  loadModels,
  handleSwitchModel,
} = useChat()

// 导出对话框
const showExportDialog = ref(false)

// 判断是否是最后一条AI消息（且已完成回复）
function isLastAiMessage(index: number): boolean {
  if (messages.value.length === 0) return false
  const lastMsg = messages.value[messages.value.length - 1]
  return lastMsg.role === 'ai' && lastMsg.content !== '' && index === messages.value.length - 1
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
      dialogId.value = null
      currentDialogName.value = '新对话'
      messages.value = [getWelcomeMessage()]
      clearFile()
    }
  },
  { immediate: true }
)

onMounted(() => {
  scrollToBottom()
  loadModels()
})

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
  background-color: #f8f9fb;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* 工具栏样式 */
.chat-toolbar {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  padding: 8px 20px;
  flex-shrink: 0;
}

.toolbar-left {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-icon-btn {
  width: 32px !important;
  height: 32px !important;
  border: none !important;
  background: transparent !important;
  color: #64748b !important;
  padding: 0 !important;
}

.toolbar-icon-btn:hover {
  color: #34d399 !important;
  background: rgba(52, 211, 153, 0.08) !important;
}

.toolbar-icon-btn:disabled {
  color: #cbd5e1 !important;
  background: transparent !important;
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
  overflow: hidden;
}

.dialog-title {
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.toolbar-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px 24px;
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
</style>
