import request from '@/utils/request'
import type {
  Product,
  CreateProductRequest,
  UpdateProductRequest,
  ProductQueryParams,
  PaginatedResponse
} from '@/types/product'

// 获取商品列表
export function getProducts(params?: ProductQueryParams) {
  return request<PaginatedResponse<Product>>({
    url: '/products',
    method: 'get',
    params
  })
}

// 获取单个商品详情
export function getProductDetail(productId: number) {
  return request<Product>({
    url: `/products/${productId}`,
    method: 'get'
  })
}

// 创建商品
export function createProduct(data: CreateProductRequest) {
  return request<Product>({
    url: '/products',
    method: 'post',
    data
  })
}

// 更新商品
export function updateProduct(productId: number, data: UpdateProductRequest) {
  return request<Product>({
    url: `/products/${productId}`,
    method: 'put',
    data
  })
}

// 删除商品
export function deleteProduct(productId: number) {
  return request<void>({
    url: `/products/${productId}`,
    method: 'delete'
  })
}
