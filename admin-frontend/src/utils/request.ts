import axios from 'axios'
import type { AxiosResponse, AxiosRequestConfig } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL as string,
  timeout: 15000 // 请求超时时间
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      // 设置JWT令牌
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error(error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // HTTP状态码为 2xx 时
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status } = error.response

      // 401: 未授权 - 跳转到登录页
      if (status === 401) {
        ElMessageBox.confirm('您的登录状态已过期，请重新登录', '登录过期', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          localStorage.removeItem('token')
          router.push('/login')
        })
      }
      // 其他错误
      else {
        const message = error.response.data?.message || '请求错误'
        ElMessage({
          message,
          type: 'error',
          duration: 5 * 1000
        })
      }
    } else {
      ElMessage({
        message: '网络连接异常，请检查网络',
        type: 'error',
        duration: 5 * 1000
      })
    }
    return Promise.reject(error)
  }
)

export default service
