<template>
  <div class="chat-footer">
    <div class="input-wrapper">
      <!-- 文件预览 -->
      <div v-if="uploadedFile" class="file-preview">
        <el-tag closable @close="$emit('clearFile')" type="info">
          <el-icon><Document /></el-icon>
          {{ uploadedFile.name }}
        </el-tag>
      </div>

      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入消息... (Ctrl+Enter 发送)"
        @keyup.ctrl.enter="$emit('sendMessage')"
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
            @click="$emit('sendMessage')"
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
            @click="$emit('stopGeneration')"
            class="stop-button"
          >
            <el-icon><CircleClose /></el-icon>
            停止生成
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Document, Upload, Promotion, CircleClose } from '@element-plus/icons-vue'

const inputMessage = defineModel<string>('inputMessage', { required: true })

defineProps<{
  sending: boolean
  isGenerating: boolean
  uploadedFile: File | null
}>()

const emit = defineEmits<{
  sendMessage: []
  stopGeneration: []
  clearFile: []
  fileChange: [file: any]
}>()

function handleFileChange(uploadFileItem: any) {
  emit('fileChange', uploadFileItem)
}
</script>

<style scoped>
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
