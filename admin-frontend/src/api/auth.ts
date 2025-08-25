import request from '@/utils/request'

// 类型定义
export interface LoginData {
  username: string
  password: string
}

export interface AdminInfo {
  id: number
  username: string
  last_login_time: string
  created_at: string
}

// API响应类型
export interface LoginResponse {
  access_token: string
  token_type: string
  admin: AdminInfo
}

// 管理员登录
export function login(data: LoginData): Promise<LoginResponse> {
  return request({
    url: '/login',
    method: 'post',
    data
  })
}

// 获取当前管理员信息
export function getAdminInfo(): Promise<AdminInfo> {
  return request({
    url: '/me',
    method: 'get'
  })
}

// 获取所有管理员
export function getAdmins(params?: { skip?: number; limit?: number }) {
  return request({
    url: '/admins',
    method: 'get',
    params
  })
}

// 创建管理员
export function createAdmin(data: LoginData) {
  return request({
    url: '/admins',
    method: 'post',
    data
  })
}

// 更新管理员
export function updateAdmin(adminId: number, data: { password: string }) {
  return request({
    url: `/admins/${adminId}`,
    method: 'put',
    data
  })
}

// 删除管理员
export function deleteAdmin(adminId: number) {
  return request({
    url: `/admins/${adminId}`,
    method: 'delete'
  })
}
