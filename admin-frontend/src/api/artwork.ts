import request from '@/utils/request'

// 类型定义
export interface Artwork {
  id: number
  user_id: number
  style_id: number
  source_image_url: string
  result_image_url: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  is_public: boolean
  likes_count: number
  views_count: number
  error_message?: string
  created_at: string
  updated_at: string
  // 关联数据可能为null，因为有些接口可能不返回这些数据
  user?: {
    nickname: string
    avatar_url: string
  } | null
  style?: {
    name: string
    category: string
  } | null
}

// API响应类型
export interface ArtworksResponse {
  items: Artwork[]
  total: number
}

// 获取作品列表
export function getArtworks(params?: {
  skip?: number
  limit?: number
  status?: string
  is_public?: boolean
  user_id?: number
  style_id?: number
}): Promise<ArtworksResponse> {
  return request({
    url: '/artworks',
    method: 'get',
    params
  })
}

// 获取作品详情
export function getArtworkDetail(artworkId: number): Promise<Artwork> {
  return request({
    url: `/artworks/${artworkId}`,
    method: 'get'
  })
}

// 更新作品状态
export function updateArtwork(artworkId: number, data: { status?: string; is_public?: boolean }) {
  return request({
    url: `/artworks/${artworkId}`,
    method: 'put',
    data
  })
}

// 删除作品
export function deleteArtwork(artworkId: number) {
  return request({
    url: `/artworks/${artworkId}`,
    method: 'delete'
  })
}
