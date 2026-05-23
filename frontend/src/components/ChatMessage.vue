<template>
  <div :class="['message', msg.role]">
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
          @click="$emit('toggleThinking', index)"
        >
          <el-icon><View /></el-icon>
          {{ expanded ? '隐藏思考过程' : '查看思考过程' }}
        </el-button>
      </div>
      <!-- 思考过程展示区域 -->
      <div v-if="msg.thinkingSteps && msg.thinkingSteps.length > 0 && expanded" class="thinking-steps">
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
</template>

<script setup lang="ts">
import { User, Service, View } from '@element-plus/icons-vue'
import { formatMessage, formatToolName, formatToolInput } from '../composables/useMarkdown'
import type { Message } from '../types/chat'

defineProps<{
  msg: Message
  index: number
  expanded: boolean
}>()

defineEmits<{
  toggleThinking: [index: number]
}>()
</script>

<style scoped>
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

/* 报告占位容器（加载中状态） */
.message-text :deep(.report-card-placeholder) {
  border-radius: 12px;
  margin: 8px 0;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  background: #fafbfc;
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
</style>
