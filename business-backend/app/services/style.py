from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, or_
import base64
import uuid
import time
from io import BytesIO

from app.models.style import Style
from app.models.artwork import Artwork
from app.models.category import StyleCategory
from app.schemas.style import StyleCreate, StyleUpdate
from utils.cos_handler import cos_handler
from app.db.utils import get_base_query, soft_delete


class StyleService:
    @staticmethod
    def create(db: Session, style_create: StyleCreate) -> Style:
        """
        创建新风格，上传预览图和参考图到腾讯云COS
        """
        # 创建风格数据副本，避免修改原始数据
        style_data = style_create.dict()
        
        # 如果提供了base64预览图，上传到COS
        preview_url = style_data.get('preview_url')
        if preview_url and preview_url.startswith('data:image'):
            try:
                # 从base64中提取内容类型和图像数据
                content_type = preview_url.split(';')[0].split(':')[1]  # 例如：image/png
                base64_data = preview_url.split(',')[1]
                
                # 解码base64得到图像数据
                image_data = base64.b64decode(base64_data)
                
                # 生成对象存储路径
                timestamp = int(time.time())
                random_str = uuid.uuid4().hex[:8]
                file_ext = ".png" if "png" in content_type else ".jpg"
                object_key = f"styles/{timestamp}_{random_str}{file_ext}"
                
                # 上传到COS
                cos_url = cos_handler.upload_bytes(image_data, object_key, content_type)
                
                # 使用COS返回的URL替换base64数据
                style_data['preview_url'] = cos_url
                
            except Exception as e:
                # 异常处理，如果上传失败则继续，但需要记录错误
                print(f"上传预览图到COS失败: {str(e)}")
                style_data['preview_url'] = None
        
        # 如果提供了base64参考图，上传到COS
        reference_image_url = style_data.get('reference_image_url')
        if reference_image_url and reference_image_url.startswith('data:image'):
            try:
                # 从base64中提取内容类型和图像数据
                content_type = reference_image_url.split(';')[0].split(':')[1]  # 例如：image/png
                base64_data = reference_image_url.split(',')[1]
                
                # 解码base64得到图像数据
                image_data = base64.b64decode(base64_data)
                
                # 生成对象存储路径
                timestamp = int(time.time())
                random_str = uuid.uuid4().hex[:8]
                file_ext = ".png" if "png" in content_type else ".jpg"
                object_key = f"styles/reference/{timestamp}_{random_str}{file_ext}"
                
                # 上传到COS
                cos_url = cos_handler.upload_bytes(image_data, object_key, content_type)
                
                # 使用COS返回的URL替换base64数据
                style_data['reference_image_url'] = cos_url
                
            except Exception as e:
                # 异常处理，如果上传失败则继续，但需要记录错误
                print(f"上传参考图到COS失败: {str(e)}")
                style_data['reference_image_url'] = None
        
        # 创建风格记录
        db_style = Style(**style_data)
        db.add(db_style)
        db.commit()
        db.refresh(db_style)
        return db_style
    
    @staticmethod
    def get_by_id(db: Session, style_id: int) -> Optional[Style]:
        """
        通过ID获取风格，包括分类信息
        """
        return get_base_query(db, Style).options(joinedload(Style.category)).filter(Style.id == style_id).first()
    
    @staticmethod
    def get_all(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
        category_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Style]:
        """
        获取所有风格，支持分页和筛选
        """
        query = get_base_query(db, Style).options(joinedload(Style.category))
        
        # 筛选条件
        if is_active is not None:
            query = query.filter(Style.is_active == is_active)
        
        if category:
            query = query.filter(Style.category == category)
            
        if category_id:
            query = query.filter(Style.category_id == category_id)
        
        if search:
            query = query.filter(
                or_(
                    Style.name.ilike(f"%{search}%"),
                    Style.description.ilike(f"%{search}%")
                )
            )
        
        # 排序
        query = query.order_by(Style.sort_order.asc(), Style.id.asc())
        
        # 分页
        styles = query.offset(skip).limit(limit).all()
        
        return styles
    
    @staticmethod
    def update(db: Session, style_id: int, style_update: StyleUpdate) -> Optional[Style]:
        """
        更新风格，处理预览图和参考图上传
        """
        db_style = get_base_query(db, Style).filter(Style.id == style_id).first()
        if not db_style:
            return None
        
        # 创建风格数据副本，避免修改原始数据
        style_data = style_update.dict(exclude_unset=True)
        
        # 如果提供了base64预览图，上传到COS
        preview_url = style_data.get('preview_url')
        if preview_url and isinstance(preview_url, str) and preview_url.startswith('data:image'):
            try:
                # 从base64中提取内容类型和图像数据
                content_type = preview_url.split(';')[0].split(':')[1]  # 例如：image/png
                base64_data = preview_url.split(',')[1]
                
                # 解码base64得到图像数据
                image_data = base64.b64decode(base64_data)
                
                # 生成对象存储路径
                timestamp = int(time.time())
                random_str = uuid.uuid4().hex[:8]
                file_ext = ".png" if "png" in content_type else ".jpg"
                object_key = f"styles/{timestamp}_{random_str}{file_ext}"
                
                # 上传到COS
                cos_url = cos_handler.upload_bytes(image_data, object_key, content_type)
                
                # 使用COS返回的URL替换base64数据
                style_data['preview_url'] = cos_url
                
            except Exception as e:
                # 异常处理，如果上传失败则继续，但不更新预览图
                print(f"上传预览图到COS失败: {str(e)}")
                del style_data['preview_url']  # 避免使用原始base64更新数据库
        
        # 如果提供了base64参考图，上传到COS
        reference_image_url = style_data.get('reference_image_url')
        if reference_image_url and isinstance(reference_image_url, str) and reference_image_url.startswith('data:image'):
            try:
                # 从base64中提取内容类型和图像数据
                content_type = reference_image_url.split(';')[0].split(':')[1]  # 例如：image/png
                base64_data = reference_image_url.split(',')[1]
                
                # 解码base64得到图像数据
                image_data = base64.b64decode(base64_data)
                
                # 生成对象存储路径
                timestamp = int(time.time())
                random_str = uuid.uuid4().hex[:8]
                file_ext = ".png" if "png" in content_type else ".jpg"
                object_key = f"styles/reference/{timestamp}_{random_str}{file_ext}"
                
                # 上传到COS
                cos_url = cos_handler.upload_bytes(image_data, object_key, content_type)
                
                # 使用COS返回的URL替换base64数据
                style_data['reference_image_url'] = cos_url
                
            except Exception as e:
                # 异常处理，如果上传失败则继续，但不更新参考图
                print(f"上传参考图到COS失败: {str(e)}")
                del style_data['reference_image_url']  # 避免使用原始base64更新数据库
        
        # 更新属性
        for key, value in style_data.items():
            setattr(db_style, key, value)
        
        db.commit()
        db.refresh(db_style)
        return db_style
    
    @staticmethod
    def delete(db: Session, style_id: int) -> bool:
        """
        软删除风格
        """
        db_style = get_base_query(db, Style).filter(Style.id == style_id).first()
        if not db_style:
            return False
        
        # 软删除记录
        return soft_delete(db, db_style)
    
    @staticmethod
    def count(db: Session, is_active: Optional[bool] = None) -> int:
        """
        计算风格总数
        """
        query = get_base_query(db, Style)
        
        if is_active is not None:
            query = query.filter(Style.is_active == is_active)
            
        return query.with_entities(func.count(Style.id)).scalar() 