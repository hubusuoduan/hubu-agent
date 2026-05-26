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
  ;(window as any).__downloadFile = (filePath: string) => {
    const token = localStorage.getItem('access_token') || ''
    const url = `/api/v1/workspace/download/${filePath}?token=${encodeURIComponent(token)}`
    window.open(url, '_blank')
  }
}

// 异步加载文件卡片（查询后端判断文件格式，决定渲染预览图还是下载卡片）
export function loadChartPreviews() {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      // 1. 处理图片预览容器（来自 ![alt](url) 语法）
      const previews = document.querySelectorAll('.file-card-preview[data-file-path]')
      previews.forEach((el) => {
        const filePath = (el as HTMLElement).dataset.filePath
        if (!filePath || (el as HTMLElement).dataset.loaded) return
        ;(el as HTMLElement).dataset.loaded = 'true'
        const token = localStorage.getItem('access_token') || ''
        fetch(`/api/v1/workspace/download/${filePath}?token=${encodeURIComponent(token)}`)
          .then(res => {
            if (!res.ok) throw new Error('加载失败')
            return res.blob()
          })
          .then(blob => {
            const blobUrl = URL.createObjectURL(blob)
            el.innerHTML = `<img src="${blobUrl}" alt="预览" onclick="window.__previewImage('${blobUrl}')" />`
          })
          .catch(() => {
            el.innerHTML = '<div class="file-card-preview-error">预览加载失败</div>'
          })
      })

      // 2. 处理占位容器（查询 API 判断文件格式）
      const placeholders = document.querySelectorAll('.file-card-placeholder[data-file-path]')
      placeholders.forEach((el) => {
        const filePath = (el as HTMLElement).dataset.filePath
        if (!filePath || (el as HTMLElement).dataset.loaded) return
        ;(el as HTMLElement).dataset.loaded = 'true'
        const icon = (el as HTMLElement).dataset.icon || '📄'
        const title = (el as HTMLElement).dataset.title || '文件已生成'
        const desc = (el as HTMLElement).dataset.desc || '点击右侧按钮下载文件'
        const token = localStorage.getItem('access_token') || ''

        fetch(`/api/v1/workspace/info/${filePath}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
          .then(res => {
            if (!res.ok) throw new Error('查询失败')
            return res.json()
          })
          .then(info => {
            const fileFormat = (info.format || '').toLowerCase()
            const isImage = ['png', 'jpg', 'jpeg', 'svg', 'gif', 'webp'].includes(fileFormat)

            if (isImage) {
              el.className = 'file-card-preview'
              fetch(`/api/v1/workspace/download/${filePath}?token=${encodeURIComponent(token)}`)
                .then(res => {
                  if (!res.ok) throw new Error('加载失败')
                  return res.blob()
                })
                .then(blob => {
                  const blobUrl = URL.createObjectURL(blob)
                  el.innerHTML = `<img src="${blobUrl}" alt="预览" onclick="window.__previewImage('${blobUrl}')" />`
                })
                .catch(() => {
                  el.innerHTML = '<div class="file-card-preview-error">预览加载失败</div>'
                })
            } else {
              el.className = 'file-download-card'
              el.innerHTML = `
                <div class="file-card-icon">${icon}</div>
                <div class="file-card-info">
                  <div class="file-card-title">${title}</div>
                  <div class="file-card-desc">${desc}</div>
                </div>
                <button class="file-card-btn" onclick="window.__downloadFile('${filePath}')">下载</button>`
            }
          })
          .catch(() => {
            el.className = 'file-download-card'
            el.innerHTML = `
              <div class="file-card-icon">${icon}</div>
              <div class="file-card-info">
                <div class="file-card-title">${title}</div>
                <div class="file-card-desc">${desc}</div>
              </div>
              <button class="file-card-btn" onclick="window.__downloadFile('${filePath}')">下载</button>`
          })
      })
    })
  })
}
