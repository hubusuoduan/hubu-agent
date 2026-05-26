
<template>
  <div class="workflow-graph">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ zoom: 0.9, x: 20, y: 20 }"
      :min-zoom="0.5"
      :max-zoom="1.5"
      fit-view-on-init
      class="workflow-canvas"
    >
      <Background :gap="16" :size="1" pattern-color="#e5e7eb" />
      <Controls position="bottom-right" />
      <template #node-workflow="nodeProps">
        <WorkflowNode :data="nodeProps.data" />
      </template>
    </VueFlow>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import WorkflowNode from './WorkflowNode.vue'

export interface NodeTraceInfo {
  node: string
  display_name: string
  status: 'pending' | 'running' | 'completed' | 'error'
  duration_ms?: number
  input_summary?: string
  output_summary?: string
  error?: string
}

const props = defineProps<{
  nodeTraces: Record<string, NodeTraceInfo>
  totalDurationMs?: number
}>()

// 节点定义（并行 + 汇聚布局）
// 三路并行：rag / memory / history_manager 同时执行
// 汇聚到 merge 综合处理后，交给 stream_chat_agent
const nodeDefinitions = [
  { id: 'rag', label: 'RAG 检索', icon: '🔍', x: 100, y: 0 },
  { id: 'memory', label: '长期记忆', icon: '🧠', x: 300, y: 0 },
  { id: 'history_manager', label: '历史管理', icon: '📝', x: 500, y: 0 },
  { id: 'merge', label: '综合处理', icon: '🔗', x: 300, y: 130 },
  { id: 'stream_chat_agent', label: '对话 Agent', icon: '🤖', x: 300, y: 260 },
]

// 边定义：三路并行扇出到 merge，merge 到 agent
const edgeDefinitions = [
  // 并行扇出
  { source: 'rag', target: 'merge' },
  { source: 'memory', target: 'merge' },
  { source: 'history_manager', target: 'merge' },
  // 串行
  { source: 'merge', target: 'stream_chat_agent' },
]

const nodes = computed(() =>
  nodeDefinitions.map((def) => {
    const trace = props.nodeTraces[def.id]
    return {
      id: def.id,
      type: 'workflow',
      position: { x: def.x, y: def.y },
      data: {
        label: def.label,
        icon: def.icon,
        status: trace?.status || 'pending',
        duration_ms: trace?.duration_ms,
        input_summary: trace?.input_summary,
        output_summary: trace?.output_summary,
        error: trace?.error,
      },
    }
  })
)

const edges = computed(() => {
  return edgeDefinitions.map((def) => {
    const sourceTrace = props.nodeTraces[def.source]
    const targetTrace = props.nodeTraces[def.target]
    const isActive = sourceTrace?.status === 'completed' && (targetTrace?.status === 'running' || targetTrace?.status === 'completed')
    return {
      id: `e-${def.source}-${def.target}`,
      source: def.source,
      target: def.target,
      animated: isActive,
      style: isActive ? { stroke: '#09b572', strokeWidth: 2 } : { stroke: '#d1d5db', strokeWidth: 1.5 },
    }
  })
})
</script>

<style scoped>
.workflow-graph {
  width: 100%;
  height: 100%;
  background: #fafbfc;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.workflow-canvas {
  width: 100%;
  height: 100%;
}
</style>
