
<template>
  <div class="thinking-section">
    <!-- 折叠按钮 -->
    <div class="thinking-toggle-area">
      <div class="thinking-toggle" @click="$emit('toggle')">
        <el-icon :size="14" class="thinking-icon"><View /></el-icon>
        <span>{{ expanded ? '收起执行过程' : '查看执行过程' }}</span>
        <el-icon :size="12" class="thinking-arrow" :class="{ expanded }"><ArrowRight /></el-icon>
      </div>
    </div>
    <!-- 统一按顺序展示事件 -->
    <div v-if="expanded" class="event-steps">
      <div
        v-for="(step, sIdx) in processSteps"
        :key="sIdx"
        :class="['event-row', step.stepType === 'tool' ? step.status.toLowerCase() : 'thinking']"
      >
        <!-- 工具调用步骤 -->
        <template v-if="step.stepType === 'tool'">
          <div class="event-header" @click="toggleStep(sIdx)">
            <span class="event-icon">
              <el-icon v-if="step.status === 'START'" class="is-loading"><Loading /></el-icon>
              <template v-else-if="step.status === 'END'">&#9989;</template>
              <template v-else-if="step.status === 'ERROR'">&#10060;</template>
            </span>
            <span class="event-title">{{ step.title }}</span>
            <span class="event-status">{{ statusLabel(step.status) }}</span>
            <span class="event-toggle">{{ step.show ? '收起' : '展开' }}</span>
          </div>
          <div v-if="step.show && step.message" class="event-detail">
            <pre>{{ step.message }}</pre>
          </div>
        </template>
        <!-- 思考过程步骤 -->
        <template v-else-if="step.stepType === 'thinking'">
          <div class="event-header">
            <span class="event-icon">&#128161;</span>
            <span class="event-title">思考</span>
          </div>
          <div v-if="step.content" class="event-detail">
            <pre>{{ step.content }}</pre>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { View, ArrowRight, Loading } from '@element-plus/icons-vue'
import type { ProcessStep } from '../types/chat'

const props = defineProps<{
  processSteps: ProcessStep[]
  expanded: boolean
}>()

defineEmits<{
  toggle: []
}>()

function toggleStep(idx: number) {
  const step = props.processSteps[idx]
  if (step && step.stepType === 'tool') {
    step.show = !step.show
  }
}

function statusLabel(status: string) {
  if (status === 'START') return '进行中'
  if (status === 'END') return '已完成'
  if (status === 'ERROR') return '失败'
  return status
}
</script>

<style scoped>
.thinking-toggle-area {
  margin-bottom: 8px;
}

.thinking-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  background: #f3f4f6;
}

.thinking-toggle:hover {
  background: #e5e7eb;
  color: #374151;
}

.thinking-icon {
  color: #09b572;
}

.thinking-arrow {
  transition: transform 0.2s;
}

.thinking-arrow.expanded {
  transform: rotate(90deg);
}

.event-steps {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.event-steps::-webkit-scrollbar {
  width: 4px;
}

.event-steps::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.event-row {
  padding: 8px 10px;
  margin-bottom: 6px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.event-row:last-child {
  margin-bottom: 0;
}

.event-row.start {
  background: rgba(245, 158, 11, 0.06);
  border-left: 3px solid #f59e0b;
}

.event-row.end {
  background: rgba(16, 185, 129, 0.06);
  border-left: 3px solid #10b981;
}

.event-row.error {
  background: rgba(239, 68, 68, 0.06);
  border-left: 3px solid #ef4444;
}

.event-row.thinking {
  background: rgba(9, 181, 114, 0.06);
  border-left: 3px solid #09b572;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.event-icon {
  font-size: 14px;
}

.event-title {
  font-weight: 500;
  color: #374151;
  flex: 1;
}

.event-status {
  font-size: 12px;
  color: #9ca3af;
}

.event-toggle {
  font-size: 12px;
  color: #6b7280;
}

.event-detail {
  margin-top: 8px;
  padding: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.event-detail pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  color: #4b5563;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}
</style>
