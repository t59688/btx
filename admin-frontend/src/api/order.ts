import request from '@/utils/request'
import type {
  Order,
  UpdateOrderRequest,
  OrderQueryParams,
  PaginatedResponse
} from '@/types/order'

// 获取订单列表
export function getOrders(params?: OrderQueryParams) {
  return request<PaginatedResponse<Order>>({
    url: '/orders',
    method: 'get',
    params
  })
}

// 获取订单详情
export function getOrderDetail(orderId: number) {
  return request<Order>({
    url: `/orders/${orderId}`,
    method: 'get'
  })
}

// 更新订单
export function updateOrder(orderId: number, data: UpdateOrderRequest) {
  return request<{id: number, order_no: string, status: string, message: string}>({
    url: `/orders/${orderId}`,
    method: 'put',
    data
  })
}

// 删除订单
export function deleteOrder(orderId: number) {
  return request<void>({
    url: `/orders/${orderId}`,
    method: 'delete'
  })
}

// 订单退款
export function refundOrder(orderId: number) {
  return request<{order_id: number, order_no: string, status: string, message: string}>({
    url: `/orders/${orderId}/refund`,
    method: 'post'
  })
}
