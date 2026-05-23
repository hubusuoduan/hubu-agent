<template>
  <div class="chat-page">
    <!-- 工具栏 -->
    <div class="chat-toolbar">
      <div class="toolbar-left">
        <span class="page-title">{{ currentDialogName }}</span>
      </div>
      <div class="toolbar-right">
        <el-button
          v-if="Object.keys(nodeTraces).length > 0"
          size="default"
          :type="showWorkflowPanel ? 'primary' : 'info'"
          plain
          @click="showWorkflowPanel = !showWorkflowPanel"
        >
          <el-icon><View /></el-icon>
          {{ showWorkflowPanel ? '关闭追踪' : '工作流追踪' }}
        </el-button>
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
          type="success"
          plain
          @click="showExportDialog = true"
          :disabled="!dialogId"
        >
          <el-icon><Download /></el-icon>
          导出
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
        <ChatMessage
          v-for="(msg, index) in messages"
          :key="index"
          :msg="msg"
          :index="index"
          :expanded="!!thinkingExpanded[index]"
          @toggle-thinking="toggleThinking"
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
      :uploaded-file="uploadedFile"
      @send-message="sendMessage"
      @stop-generation="stopGeneration"
      @clear-file="clearFile"
      @file-change="handleFileChange"
    />

    <!-- 工作流可视化侧边栏（覆盖在右侧） -->
    <WorkflowSidebar
      :visible="showWorkflowPanel"
      :node-traces="nodeTraces"
      :total-duration-ms="workflowTotalMs"
      @close="showWorkflowPanel = false"
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
import { Delete, Loading, SwitchButton, Plus, View, Download } from '@element-plus/icons-vue'
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
  uploadedFile,
  fileContent,
  uploadingFile,
  isGenerating,
  thinkingExpanded,
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
  handleLogout,
} = useChat()

// 导出对话框
const showExportDialog = ref(false)

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
  background-color: #f0f2f5;
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
