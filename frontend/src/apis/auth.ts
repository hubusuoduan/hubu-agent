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
 * 解析JWT Token获取过期时间
 * @param token JWT Token
 * @returns 过期时间戳(毫秒)或null
 */
const getTokenExpireTime = (token: string): number | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

// Token提前刷新阈值：过期前5分钟刷新
const REFRESH_THRESHOLD = 5 * 60 * 1000

/**
 * 获取有效的访问令牌（自动刷新即将过期的Token）
 * @returns 有效的access_token
 */
export const getValidAccessToken = async (): Promise<string | null> => {
  const token = getAccessToken()
  if (!token) return null

  // 检查Token是否即将过期
  const expireTime = getTokenExpireTime(token)
  if (expireTime && Date.now() > expireTime - REFRESH_THRESHOLD) {
    try {
      return await refreshAccessToken()
    } catch {
      // 刷新失败，返回当前token，让后续401处理
      return token
    }
  }

  return token
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
  // 请求前主动刷新即将过期的Token
  const validToken = await getValidAccessToken()
  if (validToken) {
    const headers = new Headers(options.headers || {})
    headers.set('Authorization', `Bearer ${validToken}`)
    options = { ...options, headers }
  }

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

      const newOptions: RequestInit = {
        ...options,
        headers
      }

      // 如果 body 是 FormData，需要重新创建
      if (options.body instanceof FormData) {
        newOptions.body = options.body
      }

      // 使用新 token 重试请求
      response = await fetch(url, newOptions)
    } catch (refreshError) {
      console.error('Token refresh failed:', refreshError)
      // 刷新失败，跳转到登录页
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
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
