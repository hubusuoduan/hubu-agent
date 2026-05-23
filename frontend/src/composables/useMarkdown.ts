import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// Markdown 解析器实例
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code>' +
               hljs.highlight(str, { language: lang }).value +
               '</code></pre>'
      } catch (__) {}
    }
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

// 全局图片预览函数（点击图片弹出全屏查看）
export function initPreviewImage() {
  ;(window as any).__previewImage = (blobUrl: string) => {
    const overlay = document.createElement('div')
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:9999;cursor:zoom-out;'
    const img = document.createElement('img')
    img.src = blobUrl
    img.style.cssText = 'max-width:90vw;max-height:90vh;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,0.4);'
    overlay.appendChild(img)
    overlay.addEventListener('click', () => {
      document.body.removeChild(overlay)
    })
    document.body.appendChild(overlay)
  }
}

// 全局下载函数（供 v-html 中的 onclick 调用）
export function initDownloadFile() {
  ;(window as any).__downloadFile = (reportId: string) => {
    const token = localStorage.getItem('access_token') || ''
    const url = `/api/v1/report/download/${reportId}?token=${encodeURIComponent(token)}`
    window.open(url, '_blank')
  }
}

// 异步加载图表预览图片（用 fetch + blob 避免 token 认证问题）
export function loadChartPreviews() {
  const previews = document.querySelectorAll('.report-card-preview[data-report-id]')
  previews.forEach((el) => {
    const reportId = (el as HTMLElement).dataset.reportId
    if (!reportId || (el as HTMLElement).dataset.loaded) return
    ;(el as HTMLElement).dataset.loaded = 'true'
    const token = localStorage.getItem('access_token') || ''
    fetch(`/api/v1/report/download/${reportId}?token=${encodeURIComponent(token)}`)
      .then(res => {
        if (!res.ok) throw new Error('加载失败')
        return res.blob()
      })
      .then(blob => {
        const blobUrl = URL.createObjectURL(blob)
        el.innerHTML = `<img src="${blobUrl}" alt="图表预览" onclick="window.__previewImage('${blobUrl}')" />`
      })
      .catch(() => {
        el.innerHTML = '<div class="report-card-preview-error">预览加载失败</div>'
      })
  })
}

// 格式化工具名称
export function formatToolName(toolName: string): string {
  const nameMap: Record<string, string> = {
    'web_search': '网络搜索',
    'knowledge_search': '知识库搜索',
    'calculator': '计算器',
    'code_runner': '代码执行',
    'chart_generator': '图表生成',
    'report_generator': '报告生成',
    'web_scraper': '网页抓取',
    'memory_search': '记忆搜索'
  }
  return nameMap[toolName] || toolName
}

// 格式化工具输入（截断过长内容）
export function formatToolInput(input: string): string {
  try {
    const parsed = JSON.parse(input)
    const formatted = JSON.stringify(parsed, null, 2)
    return formatted.length > 300 ? formatted.slice(0, 300) + '...' : formatted
  } catch {
    return input.length > 300 ? input.slice(0, 300) + '...' : input
  }
}

// 格式化消息内容（支持 Markdown 和代码高亮、报告下载卡片）
export function formatMessage(content: string): string {
  const isChart = content.includes('📊') || content.includes('图表生成成功')
  const cardIcon = isChart ? '📊' : '📄'
  const cardTitle = isChart ? '图表文件已生成' : '报告文件已生成'
  const cardDesc = isChart ? '点击右侧按钮下载图表' : '点击右侧按钮下载报告'

  // 生成下载卡片
  function makeDownloadCard(reportId: string): string {
    if (isChart) {
      return `<div class="report-card-preview" data-report-id="${reportId}">
        <div class="report-card-preview-loading">加载中...</div>
      </div>`
    }
    return `<div class="report-download-card" data-report-id="${reportId}">
      <div class="report-card-icon">${cardIcon}</div>
      <div class="report-card-info">
        <div class="report-card-title">${cardTitle}</div>
        <div class="report-card-desc">${cardDesc}</div>
      </div>
      <button class="report-card-btn" onclick="window.__downloadFile('${reportId}')">下载</button>
    </div>`
  }

  // 用 Set 记录已处理的 reportId，避免重复生成卡片
  const processedIds = new Set<string>()

  // 1. 处理 markdown 图片语法 ![alt](/api/v1/report/download/xxx)
  let processed = content.replace(
    /!\[[^\]]*\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  // 2. 处理普通链接 [文字](/api/v1/report/download/xxx)
  processed = processed.replace(
    /\[[^\]]*\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  // 3. 处理纯文本下载链接
  processed = processed.replace(
    /(?:🔗\s*)?下载链接[：:]\s*\/api\/v1\/report\/download\/([a-zA-Z0-9]+)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  // 4. 处理裸链接 /api/v1/report/download/xxx
  processed = processed.replace(
    /(?<!\(|\[)\/api\/v1\/report\/download\/([a-zA-Z0-9]+)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makeDownloadCard(reportId)
    }
  )

  return md.render(processed)
}
