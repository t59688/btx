from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_

from app.models.category import StyleCategory
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.db.utils import get_base_query, soft_delete


class CategoryService:
    @staticmethod
    def create(db: Session, category_create: CategoryCreate) -> StyleCategory:
        """
        创建新分类
        """
        # 创建分类数据
        db_category = StyleCategory(**category_create.dict())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    
    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[StyleCategory]:
        """
        通过ID获取分类
        """
        return get_base_query(db, StyleCategory).filter(StyleCategory.id == category_id).first()
    
    @staticmethod
    def get_all(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[StyleCategory]:
        """
        获取所有分类，支持分页和筛选
        """
        query = get_base_query(db, StyleCategory)
        
        # 筛选条件
        if is_active is not None:
            query = query.filter(StyleCategory.is_active == is_active)
        
        if search:
            query = query.filter(
                or_(
                    StyleCategory.name.ilike(f"%{search}%"),
                    StyleCategory.description.ilike(f"%{search}%")
                )
            )
        
        # 排序
        query = query.order_by(StyleCategory.sort_order.asc(), StyleCategory.id.asc())
        
        # 分页
        categories = query.offset(skip).limit(limit).all()
        
        return categories
    
    @staticmethod
    def update(db: Session, category_id: int, category_update: CategoryUpdate) -> Optional[StyleCategory]:
        """
        更新分类
        """
        db_category = get_base_query(db, StyleCategory).filter(StyleCategory.id == category_id).first()
        if not db_category:
            return None
        
        # 创建分类数据副本，避免修改原始数据
        category_data = category_update.dict(exclude_unset=True)
        
        # 更新属性
        for key, value in category_data.items():
            setattr(db_category, key, value)
        
        db.commit()
        db.refresh(db_category)
        return db_category
    
    @staticmethod
    def delete(db: Session, category_id: int) -> bool:
        """
        软删除分类
        """
        db_category = get_base_query(db, StyleCategory).filter(StyleCategory.id == category_id).first()
        if not db_category:
            return False
        
        # 软删除记录
        return soft_delete(db, db_category)
    
    @staticmethod
    def count(db: Session, is_active: Optional[bool] = None) -> int:
        """
        计算分类总数
        """
        query = get_base_query(db, StyleCategory)
        
        if is_active is not None:
            query = query.filter(StyleCategory.is_active == is_active)
            
        return query.with_entities(func.count(StyleCategory.id)).scalar() 