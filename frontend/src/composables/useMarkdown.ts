/**
 * Markdown 工具函数
 *
 * 已拆分为 utils/ 目录下的子模块：
 * - utils/markdown: MarkdownIt 实例 + formatMessage
 * - utils/fileCard: 文件卡片预览/下载
 * - utils/toolFormat: 工具名称/输入格式化
 *
 * 此文件保留作为兼容入口
 */
export { formatMessage } from '../utils/markdown'
export { initPreviewImage, initDownloadFile, loadChartPreviews } from '../utils/fileCard'
export { formatToolName, formatToolInput } from '../utils/toolFormat'
