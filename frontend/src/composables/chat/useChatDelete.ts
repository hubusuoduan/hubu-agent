import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { batchDeleteMessages } from '../../apis/chat'
import type { Message } from '../../types/chat'

export function useChatDelete(
  messages: { value: Message[] },
  dialogId: { value: string | null },
  getWelcomeMessage: () => Message,
) {
  const isDeleteMode = ref(false)
  const selectedMessageIds = ref<Set<string>>(new Set())

  function enterDeleteMode() {
    isDeleteMode.value = true
    selectedMessageIds.value = new Set()
  }

  function exitDeleteMode() {
    isDeleteMode.value = false
    selectedMessageIds.value = new Set()
  }

  function toggleMessageSelection(msgId: string) {
    if (selectedMessageIds.value.has(msgId)) {
      selectedMessageIds.value.delete(msgId)
    } else {
      selectedMessageIds.value.add(msgId)
    }
    // 触发响应式更新
    selectedMessageIds.value = new Set(selectedMessageIds.value)
  }

  function toggleSelectAll() {
    const allIds = messages.value
      .filter(m => m.id)
      .map(m => m.id!)
    if (allIds.length > 0 && selectedMessageIds.value.size === allIds.length) {
      selectedMessageIds.value = new Set()
    } else {
      selectedMessageIds.value = new Set(allIds)
    }
  }

  async function confirmBatchDelete() {
    if (selectedMessageIds.value.size === 0) {
      ElMessage.warning('请选择要删除的消息')
      return
    }

    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedMessageIds.value.size} 条消息吗？删除后无法恢复。`,
        '批量删除',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      const idsToDelete = Array.from(selectedMessageIds.value)
      if (idsToDelete.length > 0 && dialogId.value) {
        await batchDeleteMessages(dialogId.value, idsToDelete)
      }

      ElMessage.success(`成功删除 ${selectedMessageIds.value.size} 条消息`)

      // 从前端消息列表中移除已删除的消息
      messages.value = messages.value.filter(m => !m.id || !selectedMessageIds.value.has(m.id))
      if (messages.value.length === 0) {
        messages.value = [getWelcomeMessage()]
      }

      exitDeleteMode()
    } catch {
      // 用户取消
    }
  }

  return {
    isDeleteMode,
    selectedMessageIds,
    enterDeleteMode,
    exitDeleteMode,
    toggleMessageSelection,
    toggleSelectAll,
    confirmBatchDelete,
  }
}
