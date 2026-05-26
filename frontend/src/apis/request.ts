import axios, { AxiosError } from 'axios'
import router from '../router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 120000  // 上传文件等操作需要更长时间
})

// 标记是否正在刷新token
let isRefreshing = false
// 存储等待刷新的请求队列
let pendingRequests: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

// 刷新token函数
const refreshToken = async (): Promise<string> => {
  const refresh_token = localStorage.getItem('refresh_token')
  if (!refresh_token) {
    throw new Error('No refresh token')
  }

  try {
    const response = await axios.post('/api/v1/auth/refresh', {
      refresh_token
    })
    
    const { access_token, refresh_token: new_refresh_token } = response.data
    
    // 更新存储的token
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', new_refresh_token)
    
    return access_token
  } catch (error) {
    // 刷新失败，清除所有token
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    throw error
  }
}

// 处理待处理的请求
const processPendingRequests = (token: string) => {
  pendingRequests.forEach(({ resolve }) => {
    resolve(token)
  })
  pendingRequests = []
}

const rejectPendingRequests = (error: any) => {
  pendingRequests.forEach(({ reject }) => {
    reject(error)
  })
  pendingRequests = []
}

// 解析JWT Token获取过期时间
const getTokenExpireTime = (token: string): number | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp ? payload.exp * 1000 : null  // 转为毫秒
  } catch {
    return null
  }
}

// Token提前刷新阈值：过期前5分钟刷新
const REFRESH_THRESHOLD = 5 * 60 * 1000

// 请求拦截器
request.interceptors.request.use(
  async config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`

      // 主动检测Token即将过期，提前刷新
      const expireTime = getTokenExpireTime(token)
      if (expireTime && Date.now() > expireTime - REFRESH_THRESHOLD && !isRefreshing) {
        try {
          const newToken = await refreshToken()
          config.headers.Authorization = `Bearer ${newToken}`
        } catch {
          // 静默失败，让响应拦截器处理401
        }
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any
    
    // 如果是401错误且不是刷新token的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 如果已经在刷新token，将请求加入队列
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingRequests.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return request(originalRequest)
        })
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      try {
        // 尝试刷新token
        const newToken = await refreshToken()
        
        // 处理队列中的请求
        processPendingRequests(newToken)
        
        // 重试原始请求
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return request(originalRequest)
      } catch (refreshError) {
        // 刷新失败，拒绝所有队列请求
        rejectPendingRequests(refreshError)
        
        // 跳转到登录页
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        router.push('/login')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default request
