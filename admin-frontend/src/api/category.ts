import request from '@/utils/request'

// 分类API的URL前缀
const apiPrefix = '/categories'

/**
 * 获取分类列表
 * @param params 查询参数
 */
export function getCategories(params?: {
  page?: number
  limit?: number
  name?: string
  is_active?: boolean
}) {
  return request({
    url: apiPrefix,
    method: 'get',
    params
  })
}

/**
 * 创建分类
 * @param data 分类数据
 */
export function createCategory(data: {
  name: string
  description?: string
  icon?: string
  color?: string
  sort_order?: number
}) {
  return request({
    url: apiPrefix,
    method: 'post',
    data
  })
}

/**
 * 更新分类
 * @param id 分类ID
 * @param data 分类更新数据
 */
export function updateCategory(id: number, data: {
  name?: string
  description?: string
  icon?: string
  color?: string
  sort_order?: number
  is_active?: boolean
}) {
  return request({
    url: `${apiPrefix}/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除分类
 * @param id 分类ID
 */
export function deleteCategory(id: number) {
  return request({
    url: `${apiPrefix}/${id}`,
    method: 'delete'
  })
}
