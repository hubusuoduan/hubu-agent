
<template>
  <div :class="['workflow-node', data.status, { 'background-node': data.isBackground, 'user-agent-node': data.isUserAgent }]">
    <div v-if="data.isBackground" class="node-bg-badge">{{ data.bgLabel || '后台异步' }}</div>
    <div class="node-header">
      <span class="node-icon">{{ data.icon }}</span>
      <span class="node-label">{{ data.label }}</span>
      <span v-if="data.status === 'running'" class="node-spinner">
        <span class="spinner"></span>
      </span>
      <span v-else-if="data.status === 'completed'" class="node-check">✓</span>
      <span v-else-if="data.status === 'error'" class="node-error-icon">✗</span>
    </div>
    <div v-if="data.duration_ms !== undefined && data.status === 'completed'" class="node-duration">
      {{ data.duration_ms }}ms
    </div>
    <div v-if="data.status === 'error' && data.error" class="node-error-msg">
      {{ data.error }}
    </div>
    <!-- 展开/折叠详情 -->
    <div v-if="data.status === 'completed' && (data.input_summary || data.output_summary)" class="node-details-toggle">
      <span class="toggle-btn" @click="expanded = !expanded">
        {{ expanded ? '收起' : '详情' }}
      </span>
    </div>
    <div v-if="expanded && data.status === 'completed'" class="node-details">
      <div v-if="data.input_summary" class="detail-item">
        <span class="detail-label">输入:</span>
        <span class="detail-value">{{ data.input_summary }}</span>
      </div>
      <div v-if="data.output_summary" class="detail-item">
        <span class="detail-label">输出:</span>
        <span class="detail-value">{{ data.output_summary }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  data: {
    label: string
    icon: string
    status: 'pending' | 'running' | 'completed' | 'error'
    duration_ms?: number
    input_summary?: string
    output_summary?: string
    error?: string
    isBackground?: boolean
    bgLabel?: string
  }
}>()

const expanded = ref(false)
</script>

<style scoped>
.workflow-node {
  min-width: 180px;
  padding: 10px 16px;
  border-radius: 10px;
  background: #fff;
  border: 2px solid #e5e7eb;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  font-size: 13px;
}

.workflow-node.pending {
  opacity: 0.55;
  border-color: #d1d5db;
}

.workflow-node.running {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15), 0 2px 8px rgba(59, 130, 246, 0.12);
  background: #eff6ff;
}

.workflow-node.completed {
  border-color: #09b572;
  box-shadow: 0 0 0 2px rgba(9, 181, 114, 0.1);
  background: #f0fdf4;
}

.workflow-node.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.12);
  background: #fef2f2;
}

/* 后台异步节点样式 */
.workflow-node.background-node {
  border-style: dashed;
  border-color: #c4b5fd;
  background: #faf5ff;
}

.workflow-node.background-node.pending {
  border-color: #c4b5fd;
  opacity: 0.6;
}

.workflow-node.background-node.running {
  border-color: #8b5cf6;
  border-style: dashed;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.12), 0 2px 8px rgba(139, 92, 246, 0.08);
  background: #f5f3ff;
}

.workflow-node.background-node.completed {
  border-color: #8b5cf6;
  border-style: dashed;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.08);
  background: #faf5ff;
}

.workflow-node.background-node.error {
  border-color: #ef4444;
  border-style: dashed;
}

/* 用户自建 Agent 节点样式 */
.workflow-node.user-agent-node {
  border-color: #22c55e;
  background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
}

.workflow-node.user-agent-node.pending {
  border-color: #86efac;
  opacity: 0.55;
}

.workflow-node.user-agent-node.running {
  border-color: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15), 0 2px 8px rgba(34, 197, 94, 0.12);
  background: #f0fdf4;
}

.workflow-node.user-agent-node.completed {
  border-color: #16a34a;
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.1);
  background: #f0fdf4;
}

.workflow-node.user-agent-node.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.12);
  background: #fef2f2;
}

.node-bg-badge {
  font-size: 10px;
  color: #7c3aed;
  background: #ede9fe;
  border: 1px solid #c4b5fd;
  border-radius: 4px;
  padding: 1px 6px;
  margin-bottom: 4px;
  text-align: center;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  font-size: 16px;
}

.node-label {
  font-weight: 600;
  color: #1f2937;
  flex: 1;
}

.node-spinner {
  display: inline-flex;
  align-items: center;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.node-check {
  color: #09b572;
  font-weight: 700;
  font-size: 14px;
}

.node-error-icon {
  color: #ef4444;
  font-weight: 700;
  font-size: 14px;
}

.node-duration {
  margin-top: 4px;
  font-size: 11px;
  color: #6b7280;
  padding-left: 24px;
}

.node-error-msg {
  margin-top: 4px;
  font-size: 11px;
  color: #ef4444;
  padding-left: 24px;
  word-break: break-all;
}

.node-details-toggle {
  margin-top: 4px;
  padding-left: 24px;
}

.toggle-btn {
  font-size: 11px;
  color: #3b82f6;
  cursor: pointer;
  user-select: none;
}

.toggle-btn:hover {
  text-decoration: underline;
}

.node-details {
  margin-top: 6px;
  padding: 6px 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 6px;
}

.detail-item {
  font-size: 11px;
  line-height: 1.6;
  display: flex;
  gap: 4px;
}

.detail-label {
  color: #6b7280;
  white-space: nowrap;
}

.detail-value {
  color: #374151;
  word-break: break-all;
}
</style>
