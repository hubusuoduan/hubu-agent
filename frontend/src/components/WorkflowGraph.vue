
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

export interface UserAgentNodeInfo {
  /** 节点名，如 user_translator */
  name: string
  /** 显示名，如 翻译官 */
  display_name: string
}

const props = defineProps<{
  nodeTraces: Record<string, NodeTraceInfo>
  totalDurationMs?: number
  /** 用户自建 Agent 节点列表（动态注入） */
  userAgents?: UserAgentNodeInfo[]
}>()

// 系统 Agent 定义（固定，用于动态匹配）
const SYSTEM_AGENTS = [
  { id: 'chat', label: '对话 Agent', icon: '💬' },
  { id: 'researcher', label: '检索 Agent', icon: '🔎' },
  { id: 'coder', label: '代码 Agent', icon: '💻' },
  { id: 'skill', label: '技能 Agent', icon: '📄' },
]

// 用户 Agent 图标轮换
const userAgentIcons = ['🤖', '🧩', '⚙️', '🛠️', '🌟', '🎯', '🔮', '💡']

// 动态构建节点定义：Agent 层只显示实际执行过的
const nodeDefinitions = computed(() => {
  const userAgents = props.userAgents || []
  const traces = props.nodeTraces

  // 收集实际执行过的 Agent 节点（有 trace 记录的）
  const activeAgents: { id: string; label: string; icon: string; isUserAgent: boolean }[] = []

  // 检查系统 Agent
  SYSTEM_AGENTS.forEach(sa => {
    if (traces[sa.id]) {
      activeAgents.push({ id: sa.id, label: sa.label, icon: sa.icon, isUserAgent: false })
    }
  })

  // 检查用户自建 Agent
  userAgents.forEach((ua, i) => {
    if (traces[ua.name]) {
      activeAgents.push({
        id: ua.name,
        label: ua.display_name,
        icon: userAgentIcons[i % userAgentIcons.length],
        isUserAgent: true,
      })
    }
  })

  // 动态计算 Agent 层位置（居中分布）
  const agentSpacing = 160
  const agentStartX = Math.max(60, 300 - (activeAgents.length - 1) * agentSpacing / 2)

  const defs: any[] = [
    // 第一层：并行检索（固定位置）
    { id: 'rag', label: 'RAG 检索', icon: '🔍', x: 80, y: 0 },
    { id: 'memory', label: '长期记忆', icon: '🧠', x: 300, y: 0 },
    { id: 'history_manager', label: '历史管理', icon: '📝', x: 520, y: 0 },
    // 第二层：综合处理
    { id: 'merge', label: '综合处理', icon: '🔗', x: 300, y: 120 },
    // 第三层：意图路由
    { id: 'supervisor', label: '意图路由', icon: '🎯', x: 300, y: 240 },
  ]

  // 第四层：实际执行的 Agent（动态位置）
  activeAgents.forEach((agent, i) => {
    defs.push({
      id: agent.id,
      label: agent.label,
      icon: agent.icon,
      x: agentStartX + i * agentSpacing,
      y: 370,
      isUserAgent: agent.isUserAgent,
    })
  })

  // 第五层：审查（固定位置）
  defs.push({ id: 'reviewer', label: '审查 Agent', icon: '✅', x: 300, y: 500 })
  // 后台异步：记忆提取（固定位置）
  defs.push({
    id: 'memory_extract',
    label: '记忆提取',
    icon: '💾',
    x: 620,
    y: 500,
    isBackground: true,
    bgLabel: '后台自动提取',
  })

  return defs
})

// 动态构建边定义：只连接实际执行过的 Agent
const edgeDefinitions = computed(() => {
  const userAgents = props.userAgents || []
  const traces = props.nodeTraces

  const edges: any[] = [
    // 并行扇出
    { source: 'rag', target: 'merge' },
    { source: 'memory', target: 'merge' },
    { source: 'history_manager', target: 'merge' },
    // 串行
    { source: 'merge', target: 'supervisor' },
  ]

  // supervisor → 实际执行的 Agent → reviewer
  SYSTEM_AGENTS.forEach(sa => {
    if (traces[sa.id]) {
      edges.push({ source: 'supervisor', target: sa.id })
      edges.push({ source: sa.id, target: 'reviewer' })
    }
  })

  userAgents.forEach(ua => {
    if (traces[ua.name]) {
      edges.push({ source: 'supervisor', target: ua.name })
      edges.push({ source: ua.name, target: 'reviewer' })
    }
  })

  // reviewer → memory_extract（后台异步）
  edges.push({ source: 'reviewer', target: 'memory_extract', isBackground: true })
  // reviewer → supervisor（打回循环）
  edges.push({ source: 'reviewer', target: 'supervisor', isLoop: true })

  return edges
})

const nodes = computed(() =>
  nodeDefinitions.value.map((def) => {
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
        isBackground: def.isBackground || false,
        bgLabel: def.bgLabel || '',
        isUserAgent: def.isUserAgent || false,
      },
    }
  })
)

const edges = computed(() => {
  return edgeDefinitions.value.map((def) => {
    const sourceTrace = props.nodeTraces[def.source]
    const targetTrace = props.nodeTraces[def.target]
    const isActive = sourceTrace?.status === 'completed' && (targetTrace?.status === 'running' || targetTrace?.status === 'completed')
    const isLoop = def.isLoop
    const isBackground = def.isBackground

    const edge: any = {
      id: `e-${def.source}-${def.target}`,
      source: def.source,
      target: def.target,
      animated: isActive && !isLoop && !isBackground,
      style: isActive
        ? { stroke: '#09b572', strokeWidth: 2 }
        : { stroke: '#d1d5db', strokeWidth: 1.5 },
    }

    // 循环边（reviewer → supervisor）用虚线 + 橙色
    if (isLoop) {
      edge.style = isActive
        ? { stroke: '#f59e0b', strokeWidth: 2, strokeDasharray: '6 3' }
        : { stroke: '#d1d5db', strokeWidth: 1.5, strokeDasharray: '6 3' }
      edge.animated = false
      edge.type = 'smoothstep'
    }

    // 后台异步边（reviewer → memory_extract）用虚线 + 紫色
    if (isBackground) {
      edge.style = isActive
        ? { stroke: '#8b5cf6', strokeWidth: 2, strokeDasharray: '8 4' }
        : { stroke: '#c4b5fd', strokeWidth: 1.5, strokeDasharray: '8 4' }
      edge.animated = false
      edge.type = 'smoothstep'
      edge.label = '后台异步'
      edge.labelStyle = { fill: '#8b5cf6', fontWeight: 600, fontSize: '11px' }
      edge.labelBgStyle = { fill: '#f5f3ff', stroke: '#c4b5fd', strokeWidth: 0.5 }
      edge.labelBgPadding = [4, 6] as any
      edge.labelBgBorderRadius = 4
    }

    return edge
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
