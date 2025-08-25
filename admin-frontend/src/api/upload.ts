import request from '@/utils/request'

/**
 * 上传文件
 * @param file 要上传的文件
 * @param folder 存储文件夹名称（可选）
 */
export function uploadFile(file: File, folder: string = 'common') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('folder', folder)

  return request({
    url: '/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
