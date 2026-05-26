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

export { md }

// 格式化消息内容（支持 Markdown 和代码高亮、文件下载卡片）
export function formatMessage(content: string): string {
  const processedPaths = new Set<string>()

  // 1. 处理 markdown 图片语法 ![alt](/api/v1/workspace/download/xxx)
  //    图片语法始终渲染为可预览图片
  let processed = content.replace(
    /!\[[^\]]*\]\(\/api\/v1\/workspace\/download\/([^\)]+)\)/g,
    (match, filePath) => {
      processedPaths.add(filePath)
      return `<div class="file-card-preview" data-file-path="${filePath}">
        <div class="file-card-preview-loading">加载中...</div>
      </div>`
    }
  )

  // 生成文件卡片占位
  function makePlaceholder(filePath: string): string {
    const fileName = filePath.split('/').pop() || filePath
    const ext = fileName.split('.').pop()?.toLowerCase() || ''
    const isChart = ['png', 'jpg', 'jpeg', 'svg', 'gif', 'webp'].includes(ext)
    const icon = isChart ? '📊' : '📄'
    const title = isChart ? '图表文件已生成' : '文件已生成'
    const desc = fileName
    return `<div class="file-card-placeholder" data-file-path="${filePath}" data-icon="${icon}" data-title="${title}" data-desc="${desc}">
      <div class="file-card-preview-loading">加载中...</div>
    </div>`
  }

  // 2. 处理普通链接 [文字](/api/v1/workspace/download/xxx)
  processed = processed.replace(
    /\[[^\]]*\]\(\/api\/v1\/workspace\/download\/([^\)]+)\)/g,
    (match, filePath) => {
      if (processedPaths.has(filePath)) return ''
      processedPaths.add(filePath)
      return makePlaceholder(filePath)
    }
  )

  // 3. 处理裸链接 /api/v1/workspace/download/xxx
  processed = processed.replace(
    /(?<!\(|\[)\/api\/v1\/workspace\/download\/([^\s\)\<]+)/g,
    (match, filePath) => {
      if (processedPaths.has(filePath)) return ''
      processedPaths.add(filePath)
      return makePlaceholder(filePath)
    }
  )

  // 4. 给 Markdown 渲染出的普通图片添加点击预览
  let rendered = md.render(processed)
  rendered = rendered.replace(
    /<img([^>]*)src="([^"]+)"([^>]*)\/?>/g,
    (match, before, src, after) => {
      if (match.includes('onclick')) return match
      return `<img${before}src="${src}"${after} onclick="window.__previewImage('${src}')" style="cursor:pointer;" />`
    }
  )

  return rendered
}
