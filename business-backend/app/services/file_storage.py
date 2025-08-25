import base64
import logging
import os
import uuid
from datetime import datetime
from io import BytesIO
import asyncio
from typing import Optional, Tuple
import hashlib

from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """
    文件存储服务，使用腾讯云COS
    """
    
    @staticmethod
    def get_cos_client():
        """获取腾讯云COS客户端"""
        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
        )
        return CosS3Client(config)
    
    @staticmethod
    async def upload_base64_image(base64_data: str, folder: str = "images") -> Tuple[bool, str]:
        """
        上传Base64编码的图片到腾讯云COS
        
        Args:
            base64_data: Base64编码的图片数据
            folder: 存储文件夹名称
            
        Returns:
            成功状态和URL（成功时）或错误信息（失败时）
        """
        try:
            # 检查和清理Base64字符串
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            # 解码Base64数据
            image_data = base64.b64decode(base64_data)
            
            # 计算文件MD5，用于防止重复上传
            file_md5 = hashlib.md5(image_data).hexdigest()
            
            # 生成文件名和路径
            date_folder = datetime.now().strftime("%Y%m%d")
            file_ext = "jpg"  # 默认扩展名
            file_name = f"{uuid.uuid4().hex}.{file_ext}"
            object_key = f"{settings.COS_UPLOAD_DIR}/{folder}/{date_folder}/{file_name}"
            
            # 在事件循环中异步执行上传
            loop = asyncio.get_event_loop()
            success, result = await loop.run_in_executor(
                None, 
                FileStorageService._upload_to_cos, 
                image_data,
                object_key,
                file_ext
            )
            
            if success:
                return True, f"{settings.COS_DOMAIN}/{object_key}"
            else:
                return False, result
                
        except Exception as e:
            error_msg = f"上传图片时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def _upload_to_cos(file_data: bytes, object_key: str, file_ext: str) -> Tuple[bool, str]:
        """
        实际执行上传到COS的函数
        """
        try:
            client = FileStorageService.get_cos_client()
            
            # 上传文件到COS
            response = client.put_object(
                Bucket=settings.COS_BUCKET,
                Body=BytesIO(file_data),
                Key=object_key,
                EnableMD5=True,
                ContentType=f"image/{file_ext}"
            )
            
            return True, object_key
            
        except CosServiceError as e:
            error_msg = f"COS服务错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"上传到COS时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    async def delete_file(file_url: str) -> Tuple[bool, str]:
        """
        从腾讯云COS删除文件
        
        Args:
            file_url: 文件的完整URL
            
        Returns:
            成功状态和成功信息或错误信息
        """
        try:
            # 从URL中提取对象键
            if settings.COS_DOMAIN in file_url:
                object_key = file_url.replace(f"{settings.COS_DOMAIN}/", "")
            else:
                return False, "URL格式不正确"
            
            # 在事件循环中异步执行删除
            loop = asyncio.get_event_loop()
            success, result = await loop.run_in_executor(
                None, 
                FileStorageService._delete_from_cos, 
                object_key
            )
            
            return success, result
            
        except Exception as e:
            error_msg = f"删除文件时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def _delete_from_cos(object_key: str) -> Tuple[bool, str]:
        """
        实际执行从COS删除的函数
        """
        try:
            client = FileStorageService.get_cos_client()
            
            # 删除COS中的文件
            response = client.delete_object(
                Bucket=settings.COS_BUCKET,
                Key=object_key
            )
            
            return True, "文件删除成功"
            
        except CosServiceError as e:
            error_msg = f"COS服务错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"从COS删除时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg 