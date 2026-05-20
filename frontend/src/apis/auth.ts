/**
 * Token 管理工具
 * 提供统一的 Token 刷新和认证机制
 */

/**
 * 刷新访问令牌
 * @returns 新的 access_token
 */
export const refreshAccessToken = async (): Promise<string> => {
  const refresh_token = localStorage.getItem('refresh_token')
  if (!refresh_token) {
    throw new Error('No refresh token available')
  }

  try {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token })
    })

    if (!response.ok) {
      throw new Error('Token refresh failed')
    }

    const data = await response.json()
    const { access_token, refresh_token: new_refresh_token } = data

    // 更新存储的 token
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', new_refresh_token)

    return access_token
  } catch (error) {
    // 刷新失败，清除所有 token
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    throw error
  }
}

/**
 * 带 Token 自动刷新的 Fetch 请求
 * @param url 请求 URL
 * @param options Fetch 选项
 * @returns Response 对象
 */
export const fetchWithTokenRefresh = async (
  url: string,
  options: RequestInit
): Promise<Response> => {
  // 第一次尝试请求
  let response = await fetch(url, options)

  // 如果返回 401，尝试刷新 token
  if (response.status === 401) {
    try {
      // 刷新 token
      const newToken = await refreshAccessToken()

      // 更新请求头中的 token
      const headers = new Headers(options.headers || {})
      headers.set('Authorization', `Bearer ${newToken}`)

      // 对于 FormData 需要重新创建（如果有的话）
      const newOptions: RequestInit = {
        ...options,
        headers
      }

      // 如果 body 是 FormData，需要重新创建
      if (options.body instanceof FormData) {
        newOptions.body = options.body // FormData 可以直接复用
      }

      // 使用新 token 重试请求
      response = await fetch(url, newOptions)
    } catch (refreshError) {
      console.error('Token refresh failed:', refreshError)
      // 刷新失败，跳转到登录页
      window.location.href = '/login'
      throw refreshError
    }
  }

  return response
}

/**
 * 获取当前访问令牌
 * @returns access_token 或 null
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem('access_token')
}

/**
 * 检查是否已登录
 * @returns boolean
 */
export const isAuthenticated = (): boolean => {
  return !!getAccessToken()
}

/**
 * 退出登录
 */
export const logout = (): void => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.location.href = '/login'
}
