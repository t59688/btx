import request from '@/utils/request'

// 类型定义
export interface Style {
  id: number
  name: string
  description?: string
  preview_url?: string
  reference_image_url?: string
  category?: string
  category_id?: number
  prompt?: string
  credits_cost: number
  is_active: boolean
  sort_order?: number
  created_at: string
  updated_at: string
}

export interface StyleCreate {
  name: string
  description?: string
  preview_url?: string
  reference_image_url?: string
  category?: string
  category_id?: number
  prompt?: string
  credits_cost?: number
  sort_order?: number
}

export interface StyleUpdate {
  name?: string
  description?: string
  preview_url?: string
  reference_image_url?: string
  category?: string
  category_id?: number
  prompt?: string
  credits_cost?: number
  is_active?: boolean
  sort_order?: number
}

// API响应类型
export interface ApiResponse<T> {
  items: T[]
  total: number
}

// 获取风格列表
export function getStyles(params?: {
  page?: number
  limit?: number
  name?: string
  category?: string
  category_id?: number
  is_active?: boolean
}) {
  return request({
    url: '/styles',
    method: 'get',
    params
  })
}

// 获取单个风格详情
export function getStyle(id: number) {
  return request({
    url: `/styles/${id}`,
    method: 'get'
  })
}

// 创建风格
export function createStyle(data: StyleCreate) {
  return request({
    url: '/styles',
    method: 'post',
    data
  })
}

// 更新风格
export function updateStyle(id: number, data: StyleUpdate) {
  return request({
    url: `/styles/${id}`,
    method: 'put',
    data
  })
}

// 删除风格
export function deleteStyle(id: number) {
  return request({
    url: `/styles/${id}`,
    method: 'delete'
  })
}
