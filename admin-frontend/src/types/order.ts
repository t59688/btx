// 订单状态类型
export type OrderStatus = 'pending' | 'paid' | 'completed' | 'cancelled' | 'refunded'

// 订单类型定义
export interface Order {
  id: number
  order_no: string
  user_id: number
  user_nickname: string
  user_avatar?: string
  product_id: number
  product_name: string
  product_description?: string
  product_image_url?: string
  amount: number
  credits: number
  status: OrderStatus
  payment_id?: string
  payment_time?: string
  refund_time?: string
  remark?: string
  created_at: string
  updated_at: string
}

// 订单列表查询参数
export interface OrderQueryParams {
  page?: number
  limit?: number
  status?: OrderStatus
  user_id?: number
  order_no?: string
  date_start?: string
  date_end?: string
}

// 更新订单请求参数
export interface UpdateOrderRequest {
  status?: OrderStatus
  remark?: string
}

// 分页响应结果
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}
