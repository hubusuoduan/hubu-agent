import { useChatStream } from './useChatStream'
import { useChatModels } from './useChatModels'
import { useChatWorkflow } from './useChatWorkflow'
import { useChatFiles } from './useChatFiles'
import { useChatDelete } from './useChatDelete'

/**
 * 聊天功能组合式函数
 *
 * 拆分为 5 个子模块：
 * - useChatStream: 核心消息收发、流式处理、对话管理
 * - useChatModels: 模型列表加载与切换
 * - useChatWorkflow: 工作流节点追踪
 * - useChatFiles: 文件上传管理
 * - useChatDelete: 批量删除消息
 */
export function useChat() {
  const stream = useChatStream()
  const models = useChatModels()
  const workflow = useChatWorkflow()
  const files = useChatFiles()
  const deleteMode = useChatDelete(stream.messages, stream.dialogId, stream.getWelcomeMessage)

  // 发送消息（组合各子模块的回调）
  const sendMessage = () => {
    const fileContent = files.uploadedFiles.value.length > 0
      ? files.uploadedFiles.value.map(f => '--- 文件: ' + f.file.name + ' ---\n' + f.content).join('\n\n')
      : undefined

    stream.sendMessage(fileContent, {
      onNodeEvent: workflow.handleNodeEvent,
      resetWorkflow: workflow.resetWorkflow,
      clearFile: files.clearFile,
    })
  }

  // 重新生成消息
  const regenerateMessage = (aiMessageIndex: number) => {
    stream.regenerateMessage(aiMessageIndex, {
      onNodeEvent: workflow.handleNodeEvent,
      resetWorkflow: workflow.resetWorkflow,
    })
  }

  return {
    // 核心消息状态
    messages: stream.messages,
    inputMessage: stream.inputMessage,
    sending: stream.sending,
    dialogId: stream.dialogId,
    currentDialogName: stream.currentDialogName,
    messagesRef: stream.messagesRef,
    currentAiMessageIndex: stream.currentAiMessageIndex,
    isGenerating: stream.isGenerating,
    thinkingExpanded: stream.thinkingExpanded,
    currentThinkingStep: stream.currentThinkingStep,

    // 核心消息方法
    getWelcomeMessage: stream.getWelcomeMessage,
    toggleThinking: stream.toggleThinking,
    scrollToBottom: stream.scrollToBottom,
    startNewDialog: stream.startNewDialog,
    clearChat: stream.clearChat,
    loadDialogHistory: stream.loadDialogHistory,
    stopGeneration: stream.stopGeneration,
    saveInProgressMessage: stream.saveInProgressMessage,
    handleLogout: stream.handleLogout,

    // 组合方法
    sendMessage,
    regenerateMessage,

    // 模型
    modelList: models.modelList,
    loadModels: models.loadModels,
    handleSwitchModel: models.handleSwitchModel,

    // 工作流
    showWorkflowPanel: workflow.showWorkflowPanel,
    nodeTraces: workflow.nodeTraces,
    workflowTotalMs: workflow.workflowTotalMs,
    userAgentNodes: workflow.userAgentNodes,

    // 文件
    uploadedFiles: files.uploadedFiles,
    uploadingFile: files.uploadingFile,
    handleFileChange: files.handleFileChange,
    clearFile: files.clearFile,
    removeFile: files.removeFile,

    // 批量删除
    isDeleteMode: deleteMode.isDeleteMode,
    selectedMessageIds: deleteMode.selectedMessageIds,
    enterDeleteMode: deleteMode.enterDeleteMode,
    exitDeleteMode: deleteMode.exitDeleteMode,
    toggleMessageSelection: deleteMode.toggleMessageSelection,
    toggleSelectAll: deleteMode.toggleSelectAll,
    confirmBatchDelete: deleteMode.confirmBatchDelete,
  }
}
