import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const silent = Boolean(error.config?.silent)
    const skipAuthRedirect = Boolean(error.config?.skipAuthRedirect)
    if (error.response) {
      switch (error.response.status) {
        case 401:
          if (!silent) ElMessage.error('登录已过期，请重新登录')
          if (!skipAuthRedirect) {
            localStorage.removeItem('token')
            localStorage.removeItem('username')
            router.push('/login')
          }
          break
        case 403:
          if (!silent) ElMessage.error('没有权限访问')
          break
        case 404:
          if (!silent) {
            if (typeof error.response.data?.detail === 'string' && error.response.data.detail.includes('Invalid page')) {
              ElMessage.warning('页码超出范围，已重置')
            } else {
              ElMessage.error('请求的资源不存在')
            }
          }
          break
        case 500:
          if (!silent) {
            ElMessage.error(error.response.data?.error || error.response.data?.detail || '服务器错误')
          }
          break
        default:
          if (!silent) ElMessage.error(error.response.data?.error || error.response.data?.detail || '请求失败')
      }
    } else {
      if (!silent) ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
