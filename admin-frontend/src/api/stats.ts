import request from '@/utils/request'

// 统计数据接口
export interface Statistics {
  userCount: number
  artworkCount: number
  productCount: number
  orderCount: number
  todayUsers: number
  todayArtworks: number
  todayOrders: number
  userStats: Record<string, number>
  artworkStats: Record<string, number>
  orderStats: Record<string, number>
  revenueStats: Record<string, number>
}

// 风格统计数据
export interface StyleStats {
  id: number
  name: string
  category: string
  usage_count: number
  credits_cost: number
}

// 获取统计数据
export function getStatistics() {
  return request<Statistics>({
    url: '/statistics',
    method: 'get'
  })
}

// 获取风格使用统计
export function getStyleStats() {
  return request<StyleStats[]>({
    url: '/statistics/styles',
    method: 'get'
  })
}

// 获取订单统计数据
export function getOrderStats(params?: {
  start_date?: string
  end_date?: string
}) {
  return request<{
    orderCount: number
    totalAmount: number
    refundCount: number
    refundAmount: number
    dailyStats: {
      date: string
      orderCount: number
      amount: number
    }[]
  }>({
    url: '/statistics/orders',
    method: 'get',
    params
  })
}

// 获取产品销售统计
export function getProductSalesStats() {
  return request<{
    productId: number
    productName: string
    salesCount: number
    totalAmount: number
  }[]>({
    url: '/statistics/product-sales',
    method: 'get'
  })
}
