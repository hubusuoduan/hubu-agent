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

// 异步加载报告/图表卡片（查询后端判断文件格式，决定渲染预览图还是下载卡片）
export function loadChartPreviews() {
  // 使用双重 rAF 确保 DOM 已完全渲染
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      // 1. 处理已有的图片预览容器（来自 ![alt](url) 语法）
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

      // 2. 处理占位容器（查询 API 判断文件格式）
      const placeholders = document.querySelectorAll('.report-card-placeholder[data-report-id]')
      placeholders.forEach((el) => {
        const reportId = (el as HTMLElement).dataset.reportId
        if (!reportId || (el as HTMLElement).dataset.loaded) return
        ;(el as HTMLElement).dataset.loaded = 'true'
        const icon = (el as HTMLElement).dataset.icon || '📄'
        const title = (el as HTMLElement).dataset.title || '报告文件已生成'
        const desc = (el as HTMLElement).dataset.desc || '点击右侧按钮下载报告'
        const token = localStorage.getItem('access_token') || ''

        // 先查询文件信息
        fetch(`/api/v1/report/info/${reportId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
          .then(res => {
            if (!res.ok) throw new Error('查询失败')
            return res.json()
          })
          .then(info => {
            const fileFormat = (info.file_format || '').toLowerCase()
            const isImage = ['png', 'jpg', 'jpeg', 'svg', 'gif', 'webp'].includes(fileFormat)

            if (isImage) {
              // 图片格式：渲染预览图
              el.className = 'report-card-preview'
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
            } else {
              // 非图片格式：渲染下载卡片
              el.className = 'report-download-card'
              el.innerHTML = `
                <div class="report-card-icon">${icon}</div>
                <div class="report-card-info">
                  <div class="report-card-title">${title}</div>
                  <div class="report-card-desc">${desc}</div>
                </div>
                <button class="report-card-btn" onclick="window.__downloadFile('${reportId}')">下载</button>`
            }
          })
          .catch(() => {
            // 查询失败，降级为下载卡片
            el.className = 'report-download-card'
            el.innerHTML = `
              <div class="report-card-icon">${icon}</div>
              <div class="report-card-info">
                <div class="report-card-title">${title}</div>
                <div class="report-card-desc">${desc}</div>
              </div>
              <button class="report-card-btn" onclick="window.__downloadFile('${reportId}')">下载</button>`
          })
      })
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

  // 用 Set 记录已处理的 reportId，避免重复生成卡片
  const processedIds = new Set<string>()

  // 1. 处理 markdown 图片语法 ![alt](/api/v1/report/download/xxx)
  //    图片语法始终渲染为可预览图片，不生成下载卡片
  let processed = content.replace(
    /!\[[^\]]*\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      processedIds.add(reportId)
      return `<div class="report-card-preview" data-report-id="${reportId}">
        <div class="report-card-preview-loading">加载中...</div>
      </div>`
    }
  )

  // 2/3/4. 统一生成占位容器，由 loadChartPreviews 异步决定渲染预览还是下载卡片
  function makePlaceholder(reportId: string): string {
    return `<div class="report-card-placeholder" data-report-id="${reportId}" data-icon="${cardIcon}" data-title="${cardTitle}" data-desc="${cardDesc}">
      <div class="report-card-preview-loading">加载中...</div>
    </div>`
  }

  // 2. 处理普通链接 [文字](/api/v1/report/download/xxx)
  processed = processed.replace(
    /\[[^\]]*\]\(\/api\/v1\/report\/download\/([^\)]+)\)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makePlaceholder(reportId)
    }
  )

  // 3. 处理纯文本下载链接
  processed = processed.replace(
    /(?:🔗\s*)?下载链接[：:]\s*\/api\/v1\/report\/download\/([a-zA-Z0-9]+)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makePlaceholder(reportId)
    }
  )

  // 4. 处理裸链接 /api/v1/report/download/xxx
  processed = processed.replace(
    /(?<!\(|\[)\/api\/v1\/report\/download\/([a-zA-Z0-9]+)/g,
    (match, reportId) => {
      if (processedIds.has(reportId)) return ''
      processedIds.add(reportId)
      return makePlaceholder(reportId)
    }
  )

  // 5. 给 Markdown 渲染出的普通图片添加点击预览
  let rendered = md.render(processed)
  rendered = rendered.replace(
    /<img([^>]*)src="([^"]+)"([^>]*)\/?>/g,
    (match, before, src, after) => {
      // 已经有 onclick 的不重复添加
      if (match.includes('onclick')) return match
      return `<img${before}src="${src}"${after} onclick="window.__previewImage('${src}')" style="cursor:pointer;" />`
    }
  )

  return rendered
}
