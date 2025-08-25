// 分页查询参数
export interface PageParams {
  page?: number
  per_page?: number
}

// 分页响应
export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// 下拉选项类型
export interface SelectOption {
  value: string | number
  label: string
}

// API响应结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}