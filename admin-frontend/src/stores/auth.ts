import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login, getAdminInfo } from '@/api/auth'
import type { LoginData, AdminInfo, LoginResponse } from '@/api/auth'
import router from '@/router'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const adminInfo = ref<AdminInfo | null>(null)
  const loading = ref(false)

  // 登录
  async function loginAction(loginData: LoginData) {
    try {
      loading.value = true
      const res = await login(loginData)
      token.value = res.access_token
      adminInfo.value = res.admin

      // 保存token到本地
      localStorage.setItem('token', res.access_token)

      ElMessage({
        type: 'success',
        message: '登录成功'
      })

      // 跳转到首页
      router.push('/')
    } catch (error) {
      console.error('登录失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取管理员信息
  async function getAdminInfoAction() {
    if (!token.value) return

    try {
      const res = await getAdminInfo()
      adminInfo.value = res
    } catch (error) {
      console.error('获取管理员信息失败:', error)
    }
  }

  // 登出
  function logout() {
    token.value = null
    adminInfo.value = null
    localStorage.removeItem('token')
    router.push('/login')
    ElMessage({
      type: 'success',
      message: '退出登录成功'
    })
  }

  return {
    token,
    adminInfo,
    loading,
    loginAction,
    getAdminInfoAction,
    logout
  }
})
