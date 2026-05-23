<template>
  <transition name="workflow-slide">
    <div v-if="visible" class="workflow-sidebar">
      <div class="workflow-sidebar-header">
        <span class="workflow-sidebar-title">
          <el-icon><View /></el-icon>
          工作流追踪
        </span>
        <div class="workflow-sidebar-meta">
          <span v-if="totalDurationMs > 0" class="workflow-total-time">总耗时: {{ totalDurationMs }}ms</span>
          <el-button size="small" text @click="$emit('close')">
            <el-icon><CircleClose /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="workflow-sidebar-body">
        <WorkflowGraph :node-traces="nodeTraces" :total-duration-ms="totalDurationMs" />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { View, CircleClose } from '@element-plus/icons-vue'
import WorkflowGraph from './WorkflowGraph.vue'
import type { NodeTraceInfo } from './WorkflowGraph.vue'

defineProps<{
  visible: boolean
  nodeTraces: Record<string, NodeTraceInfo>
  totalDurationMs: number
}>()

defineEmits<{
  close: []
}>()
</script>

<style scoped>
.workflow-sidebar {
  position: absolute;
  top: 0;
  right: 0;
  width: 420px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-left: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.08);
  z-index: 100;
}

.workflow-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;
}

.workflow-sidebar-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.workflow-sidebar-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.workflow-total-time {
  font-size: 12px;
  color: #09b572;
  font-weight: 500;
  background: rgba(9, 181, 114, 0.08);
  padding: 2px 8px;
  border-radius: 4px;
}

.workflow-sidebar-body {
  flex: 1;
  padding: 12px;
  overflow: hidden;
}

/* 侧边栏滑入/滑出动画 */
.workflow-slide-enter-active,
.workflow-slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.workflow-slide-enter-from,
.workflow-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.workflow-slide-enter-to,
.workflow-slide-leave-from {
  transform: translateX(0);
  opacity: 1;
}
</style>
