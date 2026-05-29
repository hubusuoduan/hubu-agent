<template>
  <div class="workflow-sidebar-wrapper">
    <!-- 收起状态的展开按钮 -->
    <transition name="workflow-toggle">
      <div
        v-if="!visible && Object.keys(nodeTraces).length > 0"
        class="workflow-toggle-btn workflow-toggle-expand"
        @click="$emit('open')"
      >
        <el-icon :size="16"><ArrowLeft /></el-icon>
      </div>
    </transition>

    <!-- 侧边栏面板 -->
    <transition name="workflow-slide">
      <div v-if="visible" class="workflow-sidebar">
        <!-- 左边缘收起按钮 -->
        <div class="workflow-collapse-btn" @click="$emit('close')">
          <el-icon :size="16"><ArrowRight /></el-icon>
        </div>
        <div class="workflow-sidebar-header">
          <span class="workflow-sidebar-title">
            <el-icon><View /></el-icon>
            工作流追踪
          </span>
          <span v-if="totalDurationMs > 0" class="workflow-total-time">总耗时: {{ totalDurationMs }}ms</span>
        </div>
        <div class="workflow-sidebar-body">
          <WorkflowGraph :node-traces="nodeTraces" :total-duration-ms="totalDurationMs" :user-agents="userAgents" />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { View, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import WorkflowGraph from './WorkflowGraph.vue'
import type { NodeTraceInfo, UserAgentNodeInfo } from './WorkflowGraph.vue'

defineProps<{
  visible: boolean
  nodeTraces: Record<string, NodeTraceInfo>
  totalDurationMs: number
  userAgents?: UserAgentNodeInfo[]
}>()

defineEmits<{
  close: []
  open: []
}>()
</script>

<style scoped>
.workflow-sidebar-wrapper {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  z-index: 100;
  pointer-events: none;
}

.workflow-sidebar-wrapper > * {
  pointer-events: auto;
}

/* 收起状态的展开按钮（右侧边缘） */
.workflow-toggle-btn {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-right: none;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  color: #6b7280;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease;
  z-index: 101;
}

.workflow-toggle-btn:hover {
  background: #f0f7ff;
  color: #409eff;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
}

/* 展开按钮动画 */
.workflow-toggle-enter-active,
.workflow-toggle-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.workflow-toggle-enter-from,
.workflow-toggle-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(10px);
}
.workflow-toggle-enter-to,
.workflow-toggle-leave-from {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}

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
}

/* 左边缘收起按钮 */
.workflow-collapse-btn {
  position: absolute;
  left: -28px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-right: none;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  color: #6b7280;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease;
  z-index: 101;
}

.workflow-collapse-btn:hover {
  background: #f0f7ff;
  color: #409eff;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
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
