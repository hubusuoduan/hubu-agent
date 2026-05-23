
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

// 节点定义（固定布局）
const nodeDefinitions = [
  { id: 'rag', label: 'RAG 检索', icon: '🔍', x: 300, y: 0 },
  { id: 'memory', label: '长期记忆', icon: '🧠', x: 300, y: 100 },
  { id: 'history_manager', label: '历史管理', icon: '📝', x: 300, y: 200 },
  { id: 'stream_chat_agent', label: '对话 Agent', icon: '🤖', x: 300, y: 300 },
  { id: 'memory_extract', label: '记忆提取', icon: '💾', x: 300, y: 400 },
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
  const ids = nodeDefinitions.map((n) => n.id)
  const result: any[] = []
  for (let i = 0; i < ids.length - 1; i++) {
    const sourceTrace = props.nodeTraces[ids[i]]
    const targetTrace = props.nodeTraces[ids[i + 1]]
    const isActive = sourceTrace?.status === 'completed' && (targetTrace?.status === 'running' || targetTrace?.status === 'completed')
    result.push({
      id: `e-${ids[i]}-${ids[i + 1]}`,
      source: ids[i],
      target: ids[i + 1],
      animated: isActive,
      style: isActive ? { stroke: '#09b572', strokeWidth: 2 } : { stroke: '#d1d5db', strokeWidth: 1.5 },
    })
  }
  return result
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
