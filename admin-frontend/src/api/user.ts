import request from '@/utils/request'

// 类型定义
export interface User {
  id: number
  openid: string
  unionid: string
  nickname: string
  avatar_url: string
  gender: number
  country: string
  province: string
  city: string
  credits: number
  is_blocked: boolean
  created_at: string
  updated_at: string
  last_login_time: string
  [key: string]: any
}

export interface CreditRecord {
  id: number
  user_id: number
  type: string
  amount: number
  balance: number
  description: string
  related_id: number | null
  created_at: string
}

// 分页响应接口
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// 获取用户列表
export function getUsers(params?: {
  skip?: number
  limit?: number
  nickname?: string
  is_blocked?: boolean
}) {
  return request({
    url: '/users',
    method: 'get',
    params
  })
}

// 获取用户详情
export function getUserDetail(userId: number) {
  return request({
    url: `/users/${userId}`,
    method: 'get'
  })
}

// 封禁/解封用户
export function blockUser(userId: number, isBlocked: boolean) {
  return request({
    url: `/users/${userId}/block`,
    method: 'put',
    data: { is_blocked: isBlocked }
  })
}

// 调整用户积分
export function adjustUserCredits(
  userId: number,
  data: {
    amount: number
    type: string
    description: string
    related_id?: number | null
  }
) {
  return request({
    url: `/users/${userId}/credits`,
    method: 'post',
    data
  })
}

// 获取用户积分记录
export function getUserCreditRecords(
  userId: number,
  params?: {
    page?: number
    per_page?: number
  }
) {
  return request({
    url: `/users/${userId}/credit-records`,
    method: 'get',
    params
  })
}
