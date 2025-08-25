import { request } from '../utils/request'

// 定义接口返回类型
interface ActivateCardKeyResponse {
  credits: number
  balance: number
  message: string
}

/**
 * 激活卡密
 * @param cardKey 卡密字符串
 */
export function activateCardKey(cardKey: string) {
  return request<ActivateCardKeyResponse>({
    url: '/card-keys/activate',
    method: 'POST',
    data: {
      card_key: cardKey
    }
  })
} 