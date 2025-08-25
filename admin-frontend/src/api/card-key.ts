import request from '@/utils/request'
import type { PageParams } from '@/types/common'

// 卡密对象类型定义
export interface CardKey {
  id: number
  card_key: string
  credits: number
  batch_no?: string
  created_by?: number
  created_at: string
  expired_at?: string
  status: 'unused' | 'used' | 'invalid'
  used_at?: string
  used_by?: number
  used_by_nickname?: string
  remark?: string
}

// 创建卡密请求参数
export interface CreateCardKeyParams {
  credits: number
  count: number
  batch_no?: string
  expired_at?: string
  remark?: string
}

// 创建卡密响应
export interface CreateCardKeyResponse {
  batch_no: string
  count: number
  credits: number
  expired_at?: string
}

// 卡密查询参数
export interface CardKeyQueryParams extends PageParams {
  status?: string
  batch_no?: string
  created_start?: string
  created_end?: string
}

// 卡密状态更新请求
export interface CardKeyStatusUpdate {
  status: 'unused' | 'used' | 'invalid'
}

// 卡密列表响应
export interface CardKeyListResponse {
  items: CardKey[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// 批量创建卡密
export function createCardKeys(data: CreateCardKeyParams) {
  return request({
    url: '/card-keys',
    method: 'post',
    data
  })
}

// 获取卡密列表
export function getCardKeys(params: CardKeyQueryParams) {
  return request({
    url: '/card-keys',
    method: 'get',
    params
  })
}

// 获取单个卡密详情
export function getCardKey(id: number) {
  return request({
    url: `/card-keys/${id}`,
    method: 'get'
  })
}

// 更新卡密状态
export function updateCardKeyStatus(id: number, data: CardKeyStatusUpdate) {
  return request({
    url: `/card-keys/${id}/status`,
    method: 'put',
    data
  })
}

// 删除卡密
export function deleteCardKey(id: number) {
  return request({
    url: `/card-keys/${id}`,
    method: 'delete'
  })
}
