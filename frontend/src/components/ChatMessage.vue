<template>
  <div :class="['message', msg.role, { 'delete-mode': isDeleteMode, 'selected': isDeleteMode && isSelected }]" @click="isDeleteMode && $emit('toggleSelect', msg.id!)">
    <!-- 批量删除模式下的复选框 -->
    <div v-if="isDeleteMode" class="delete-checkbox">
      <el-checkbox :model-value="isSelected" />
    </div>

    <!-- AI 消息：左侧头像 + 无气泡内容 -->
    <template v-if="msg.role === 'ai'">
      <div v-if="!isDeleteMode" class="ai-avatar">
        <div class="ai-avatar-inner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
      </div>
      <div class="ai-body">
        <!-- 思考过程 -->
        <ThinkingSteps
          v-if="msg.processSteps && msg.processSteps.length > 0"
          :process-steps="msg.processSteps"
          :expanded="expanded"
          @toggle="$emit('toggleThinking', index)"
        />
        <div class="message-text" v-html="formatMessage(msg.content)"></div>
        <!-- AI 消息操作栏 -->
        <div v-if="!isDeleteMode" class="message-actions">
          <div class="action-btn copy-btn" @click.stop="handleCopy">
            <el-icon :size="13"><CopyDocument /></el-icon>
          </div>
          <div v-if="isLastAiMessage && hasPrevUserMessage" class="action-btn regenerate-btn" @click.stop="$emit('regenerate', index)">
            <el-icon :size="13"><RefreshRight /></el-icon>
          </div>

          <div class="action-btn delete-msg-btn" @click.stop="$emit('enterDeleteMode')">
            <el-icon :size="13"><Delete /></el-icon>
          </div>
        </div>
      </div>
    </template>

    <!-- 用户消息：右侧气泡 -->
    <template v-else>
      <div class="user-body">
        <div class="user-bubble">
          <div class="message-text" v-html="formatMessage(msg.content)"></div>
        </div>
        <div v-if="!isDeleteMode" class="user-meta">
          <div class="user-actions">
            <div class="action-btn copy-btn" @click.stop="handleCopy">
              <el-icon :size="12"><CopyDocument /></el-icon>
            </div>
            <div class="action-btn delete-msg-btn" @click.stop="$emit('enterDeleteMode')">
              <el-icon :size="12"><Delete /></el-icon>
            </div>
          </div>
          <span class="user-time">{{ msg.time }}</span>
        </div>
      </div>
      <div v-if="!isDeleteMode" class="user-avatar">
        <el-avatar :size="32">
          <el-icon :size="18"><User /></el-icon>
        </el-avatar>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { User, RefreshRight, CopyDocument, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { formatMessage } from '../composables/useMarkdown'
import ThinkingSteps from './ThinkingSteps.vue'
import type { Message } from '../types/chat'

const props = defineProps<{
  msg: Message
  index: number
  expanded: boolean
  isDeleteMode: boolean
  isSelected: boolean
  isLastAiMessage: boolean
  hasPrevUserMessage: boolean
}>()

defineEmits<{
  toggleThinking: [index: number]
  toggleSelect: [msgId: string]
  regenerate: [index: number]
  enterDeleteMode: []
}>()

function handleCopy() {
  navigator.clipboard.writeText(props.msg.content).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}
</script>

<style scoped>
@import '../styles/chat-message.css';
</style>
