import os
import uuid
import time
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from urllib.parse import urljoin

# COS配置信息
class COSConfig:
    SECRET_ID = "xxxxxxx"
    SECRET_KEY = "xxxxxxxxxxxx"
    REGION = "ap-beijing"
    BUCKET = "xxxxxxxxx"
    DOMAIN = "https://xxxxxxxxxxxxcos.accelerate.myqcloud.com"
    UPLOAD_DIR = "xxxxxxxxxxxxxxxxx"

class COSHandler:
    """腾讯云对象存储处理工具"""
    
    def __init__(self):
        """初始化COS客户端"""
        config = CosConfig(
            Region=COSConfig.REGION,
            SecretId=COSConfig.SECRET_ID,
            SecretKey=COSConfig.SECRET_KEY,
            Scheme='https'
        )
        self.client = CosS3Client(config)
        self.bucket = COSConfig.BUCKET
    
    def upload_file(self, file_path, object_key=None):
        """上传文件到COS
        
        Args:
            file_path: 本地文件路径
            object_key: 对象存储路径，不指定则根据文件类型自动生成
            
        Returns:
            str: 文件的访问URL
        """
        # 如果未指定对象路径，则自动生成
        if not object_key:
            file_ext = os.path.splitext(file_path)[1].lower()
            timestamp = int(time.time())
            random_str = uuid.uuid4().hex[:8]
            object_key = f"{COSConfig.UPLOAD_DIR}/{timestamp}_{random_str}{file_ext}"
        
        # 上传文件
        response = self.client.upload_file(
            Bucket=self.bucket,
            LocalFilePath=file_path,
            Key=object_key,
            EnableMD5=False
        )
        
        # 返回文件的访问URL
        return self.get_file_url(object_key)
    
    def upload_bytes(self, file_bytes, object_key, content_type=None):
        """上传字节流到COS
        
        Args:
            file_bytes: 文件字节内容
            object_key: 对象存储路径
            content_type: 内容类型，例如image/jpeg
            
        Returns:
            str: 文件的访问URL
        """
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
            
        response = self.client.put_object(
            Bucket=self.bucket,
            Body=file_bytes,
            Key=object_key,
            # Headers=headers
        )
        
        return self.get_file_url(object_key)
    
    def download_file(self, object_key, local_path):
        """从COS下载文件到本地
        
        Args:
            object_key: 对象存储路径
            local_path: 本地文件保存路径
            
        Returns:
            bool: 下载是否成功
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            response['Body'].get_stream_to_file(local_path)
            return True
        except Exception as e:
            print(f"下载文件失败: {str(e)}")
            return False
    
    def get_file_url(self, object_key):
        """获取文件的访问URL
        
        Args:
            object_key: 对象存储路径
            
        Returns:
            str: 文件的访问URL
        """
        # 使用加速域名
        return urljoin(COSConfig.DOMAIN, f"/{object_key}")
    
    def delete_file(self, object_key):
        """删除COS中的文件
        
        Args:
            object_key: 对象存储路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=object_key
            )
            return True
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False

# 创建单例实例
cos_handler = COSHandler() 