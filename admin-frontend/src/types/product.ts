// 商品类型定义
export interface Product {
  id: number
  name: string
  description: string
  credits: number
  price: number
  image_url: string
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

// 创建商品请求参数
export interface CreateProductRequest {
  name: string
  description: string
  credits: number
  price: number
  image_url: string
  is_active: boolean
  sort_order: number
}

// 更新商品请求参数
export interface UpdateProductRequest {
  name?: string
  description?: string
  credits?: number
  price?: number
  image_url?: string
  is_active?: boolean
  sort_order?: number
}

// 商品列表查询参数
export interface ProductQueryParams {
  page?: number
  limit?: number
  is_active?: boolean
  search?: string
}

// 分页响应结果
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}
