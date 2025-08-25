from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.services.product import ProductService
from app.core.deps import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("", response_model=List[Product])
async def get_products(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Product]:
    """
    获取积分商品列表
    """
    products = ProductService.get_products(
        db=db,
        skip=skip,
        limit=limit,
        active_only=True
    )
    
    return products


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> Product:
    """
    获取商品详情
    """
    product = ProductService.get_product(db=db, product_id=product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    return product


# 管理员接口
@router.post("/admin", response_model=Product)
async def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Product:
    """
    创建商品（管理员）
    """
    product = ProductService.create_product(db=db, product_in=product_in)
    return product


@router.put("/admin/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Product:
    """
    更新商品（管理员）
    """
    product = ProductService.update_product(
        db=db, product_id=product_id, product_in=product_in
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    return product


@router.delete("/admin/{product_id}", response_model=Dict[str, Any])
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    删除商品（管理员）
    """
    success = ProductService.delete_product(db=db, product_id=product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    return {"message": "商品已删除"} 