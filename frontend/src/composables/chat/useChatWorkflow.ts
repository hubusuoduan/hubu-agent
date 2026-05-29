import { ref, computed } from 'vue'
import type { NodeEvent } from '../../apis/chat'
import type { NodeTraceInfo, UserAgentNodeInfo } from '../../components/WorkflowGraph.vue'

export function useChatWorkflow() {
  const showWorkflowPanel = ref(false)
  const nodeTraces = ref<Record<string, NodeTraceInfo>>({})
  const workflowTotalMs = ref<number>(0)

  // 从 nodeTraces 中自动提取用户自建 Agent 节点（user_ 前缀）
  const userAgentNodes = computed<UserAgentNodeInfo[]>(() => {
    return Object.values(nodeTraces.value)
      .filter(trace => trace.node.startsWith('user_'))
      .map(trace => ({
        name: trace.node,
        display_name: trace.display_name,
      }))
  })

  function handleNodeEvent(event: NodeEvent) {
    if (event.type === 'node_start' && event.node) {
      nodeTraces.value[event.node] = {
        node: event.node,
        display_name: event.display_name || event.node,
        status: 'running',
      }
      if (!showWorkflowPanel.value) {
        showWorkflowPanel.value = true
      }
    } else if (event.type === 'node_end' && event.node) {
      nodeTraces.value[event.node] = {
        node: event.node,
        display_name: event.display_name || event.node,
        status: 'completed',
        duration_ms: event.duration_ms,
        input_summary: event.input_summary,
        output_summary: event.output_summary,
      }
    } else if (event.type === 'node_error' && event.node) {
      nodeTraces.value[event.node] = {
        node: event.node,
        display_name: event.display_name || event.node,
        status: 'error',
        error: event.error,
      }
    } else if (event.type === 'workflow_done') {
      workflowTotalMs.value = event.total_duration_ms || 0
    }
  }

  function resetWorkflow() {
    nodeTraces.value = {}
    workflowTotalMs.value = 0
  }

  return {
    showWorkflowPanel,
    nodeTraces,
    workflowTotalMs,
    userAgentNodes,
    handleNodeEvent,
    resetWorkflow,
  }
}
