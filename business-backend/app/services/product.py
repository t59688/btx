from typing import List, Optional, Dict, Any, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)


class ProductService:
    @staticmethod
    def create_product(db: Session, product_in: ProductCreate) -> Product:
        """创建商品"""
        product = Product(
            name=product_in.name,
            description=product_in.description,
            credits=product_in.credits,
            price=product_in.price,
            image_url=product_in.image_url,
            is_active=product_in.is_active,
            sort_order=product_in.sort_order
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_product(db: Session, product_id: int) -> Optional[Product]:
        """获取单个商品"""
        return db.query(Product).filter(
            Product.id == product_id,
            Product.is_deleted == False
        ).first()

    @staticmethod
    def get_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """获取商品列表"""
        query = db.query(Product).filter(
            Product.is_deleted == False
        )
        
        if active_only:
            query = query.filter(Product.is_active == True)
            
        return query.order_by(Product.sort_order.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_product(
        db: Session,
        product_id: int,
        product_in: ProductUpdate
    ) -> Optional[Product]:
        """更新商品"""
        product = ProductService.get_product(db, product_id)
        if not product:
            return None
            
        update_data = product_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
            
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        """删除商品（软删除）"""
        product = ProductService.get_product(db, product_id)
        if not product:
            return False
            
        product.is_deleted = True
        db.commit()
        return True 