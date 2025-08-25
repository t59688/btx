from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import logging
import os
import urllib.parse
import re
from app.core.config import settings, Settings

logger = logging.getLogger(__name__)

class COSService:
    _instance = None
    _initialized = False
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(COSService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._init_client()
    
    def _init_client(self):
        """初始化腾讯云COS客户端"""
        try:
            # 从DynamicSettings获取配置，如果为空则从基础Settings获取默认值
            base_settings = Settings()
            
            secret_id = settings.COS_SECRET_ID or base_settings.COS_SECRET_ID
            secret_key = settings.COS_SECRET_KEY or base_settings.COS_SECRET_KEY
            region = settings.COS_REGION or base_settings.COS_REGION
            
            # scheme可能在基础设置中没有，使用默认值
            scheme = getattr(settings, 'COS_SCHEME', None) or getattr(base_settings, 'COS_SCHEME', 'https')
            token = None  # 使用永久密钥不需要token
            
            logger.info(f"正在初始化腾讯云COS客户端，区域：{region}")
            
            config = CosConfig(
                Region=region, 
                SecretId=secret_id, 
                SecretKey=secret_key, 
                Token=token, 
                Endpoint="cos.accelerate.myqcloud.com",
                Scheme=scheme
            )
            self._client = CosS3Client(config)
            logger.info("腾讯云COS客户端初始化成功")
        except Exception as e:
            logger.error(f"初始化腾讯云COS客户端失败: {str(e)}")
            raise
    
    def get_client(self):
        """获取COS客户端实例"""
        return self._client
    
    def generate_presigned_url(self, url, expires=600):
        """
        生成预签名URL
        
        Args:
            url: COS对象的原始URL
            expires: 链接有效期，单位为秒，默认10分钟
            
        Returns:
            预签名的临时URL
        """
        if not url:
            logger.error("无法为空URL生成预签名")
            return None
            
        try:
            # 解析URL获取bucket和key
            parsed_url = urllib.parse.urlparse(url)
            host_parts = parsed_url.netloc.split('.')
            
            # 尝试从URL中提取bucket和key
            bucket = None
            object_key = None
            
            # 检查是否是COS URL
            if 'cos' in parsed_url.netloc:
                # 通常格式为 {bucket-appid}.cos.{region}.myqcloud.com/{object-key}
                bucket_with_appid_match = re.match(r'([^.]+)', parsed_url.netloc)
                if bucket_with_appid_match:
                    bucket = bucket_with_appid_match.group(1)
                    object_key = parsed_url.path.lstrip('/')
            
            # 如果无法从URL中提取，则使用域名加路径的方式
            if not bucket or not object_key:
                # 使用默认bucket，并将整个URL路径作为对象key
                base_settings = Settings()
                bucket = settings.COS_BUCKET or base_settings.COS_BUCKET
                # 如果是自定义域名，需要使用完整路径作为object_key
                region = settings.COS_REGION or base_settings.COS_REGION
                if parsed_url.netloc not in ['cos.ap-beijing.myqcloud.com', f"{bucket}.cos.{region}.myqcloud.com"]:
                    object_key = f"{parsed_url.netloc}{parsed_url.path}".lstrip('/')
                else:
                    object_key = parsed_url.path.lstrip('/')
            
            logger.info(f"正在为 Bucket: {bucket}, Key: {object_key} 生成预签名URL")
            
            # 生成预签名URL
            response = self._client.get_presigned_url(
                Method='GET',
                Bucket=bucket,
                Key=object_key,
                Expired=expires
            )
            
            logger.info(f"成功生成预签名URL")
            return response
        except Exception as e:
            logger.error(f"生成预签名URL失败: {str(e)}")
            # 失败时返回原始URL，让调用者处理错误
            return url

# 创建单例实例
cos_service = COSService() 