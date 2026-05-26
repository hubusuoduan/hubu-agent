<template>
  <div class="chat-footer">
    <div class="input-wrapper">
      <!-- 批量删除模式 -->
      <template v-if="isDeleteMode">
        <div class="delete-mode-bar">
          <div class="delete-mode-info">
            <el-icon :size="18" color="#ef4444"><Delete /></el-icon>
            <span class="delete-mode-text">已选择 <strong>{{ selectedCount }}</strong> 条消息</span>
          </div>
          <div class="delete-mode-actions">
            <el-button size="default" @click="$emit('selectAll')">
              全选
            </el-button>
            <el-button
              size="default"
              type="danger"
              @click="$emit('confirmDelete')"
              :disabled="selectedCount === 0"
            >
              <el-icon><Delete /></el-icon>
              删除{{ selectedCount > 0 ? `(${selectedCount})` : '' }}
            </el-button>
            <el-button size="default" @click="$emit('cancelDelete')">
              取消
            </el-button>
          </div>
        </div>
      </template>
      <!-- 正常模式 -->
      <template v-else>
        <!-- 文件预览 -->
        <div v-if="uploadedFiles.length > 0" class="file-preview">
          <div
            v-for="(item, index) in uploadedFiles"
            :key="item.file.name"
            class="file-tag"
          >
            <el-icon class="file-tag-icon"><Document /></el-icon>
            <span class="file-tag-name">{{ item.file.name }}</span>
            <el-icon class="file-tag-close" @click="$emit('removeFile', index)"><Close /></el-icon>
          </div>
        </div>

        <div class="input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="输入消息..."
            @keyup.ctrl.enter="$emit('sendMessage')"
            :disabled="sending"
            resize="none"
            class="message-input"
          />
          <!-- 发送/停止按钮 -->
          <div class="send-action">
            <button
              v-if="!isGenerating"
              class="send-btn"
              @click="$emit('sendMessage')"
              :disabled="!inputMessage.trim() || sending"
            >
              <el-icon :size="18"><Top /></el-icon>
            </button>
            <button
              v-else
              class="stop-btn"
              @click="$emit('stopGeneration')"
            >
              <el-icon :size="18"><CircleClose /></el-icon>
            </button>
          </div>
        </div>

        <div class="input-actions">
          <div class="action-left">
            <el-select
              :model-value="currentModelId"
              @update:model-value="$emit('switchModel', $event)"
              placeholder="选择模型"
              size="small"
              class="model-select"
              popper-class="model-select-popper"
            >
              <template #prefix>
                <el-icon><Cpu /></el-icon>
              </template>
              <el-option
                v-for="model in modelList"
                :key="model.id"
                :label="model.name"
                :value="model.id"
              />
            </el-select>
            <el-upload
              class="file-upload"
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
              accept=".txt,.md,.pdf,.docx,.html,.htm,.csv,.json,.xml,.xlsx,.pptx,.rtf"
            >
              <button class="upload-btn" :disabled="sending">
                <el-icon><Upload /></el-icon>
                <span>上传文件</span>
              </button>
            </el-upload>
          </div>
          <div class="action-right">
            <span class="tip-text">支持 txt, pdf, docx 等格式</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Document, Upload, Top, CircleClose, Delete, Close } from '@element-plus/icons-vue'
import { Cpu } from '@element-plus/icons-vue'

const inputMessage = defineModel<string>('inputMessage', { required: true })

defineProps<{
  sending: boolean
  isGenerating: boolean
  uploadedFiles: Array<{ file: File; content: string }>
  modelList: Array<{ id: string; name: string }>
  currentModelId: string
  isDeleteMode: boolean
  selectedCount: number
}>()

const emit = defineEmits<{
  sendMessage: []
  stopGeneration: []
  clearFile: []
  removeFile: [index: number]
  fileChange: [file: any]
  switchModel: [modelId: string]
  confirmDelete: []
  cancelDelete: []
  selectAll: []
}>()

function handleFileChange(uploadFileItem: any) {
  emit('fileChange', uploadFileItem)
}
</script>

<style scoped>@import '../styles/chat-input.css';</style>
