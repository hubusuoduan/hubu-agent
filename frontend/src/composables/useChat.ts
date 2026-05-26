/**
 * 聊天功能组合式函数
 *
 * 已拆分为 composables/chat/ 目录下的子模块：
 * - useChatStream: 核心消息收发、流式处理、对话管理
 * - useChatModels: 模型列表加载与切换
 * - useChatWorkflow: 工作流节点追踪
 * - useChatFiles: 文件上传管理
 * - useChatDelete: 批量删除消息
 *
 * 此文件保留作为兼容入口，新代码请直接从 './chat' 导入
 */
export { useChat } from './chat'
