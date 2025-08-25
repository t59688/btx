import request from '@/utils/request'

// 类型定义
export interface SystemConfig {
  key: string
  value: string
  description?: string
  updated_at?: string
}

// 配置值的接口定义
export interface ConfigValue {
  value: string
  description: string
}

// API响应类型
export interface ConfigsResponse {
  [key: string]: ConfigValue
}

// 获取系统配置
export function getConfigs(params?: { prefix?: string }): Promise<ConfigsResponse> {
  return request({
    url: '/configs',
    method: 'get',
    params
  })
}

// 创建系统配置
export function createConfig(data: { config_key: string; value: string; description?: string }) {
  return request({
    url: '/configs',
    method: 'post',
    data
  })
}

// 更新系统配置
export function updateConfig(configKey: string, data: { value: string; description?: string }) {
  return request({
    url: `/configs/${configKey}`,
    method: 'put',
    data
  })
}

// 删除系统配置
export function deleteConfig(configKey: string) {
  return request({
    url: `/configs/${configKey}`,
    method: 'delete'
  })
}
