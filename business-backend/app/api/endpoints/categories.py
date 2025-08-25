from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.category import Category
from app.services.category import CategoryService

router = APIRouter()


@router.get("", response_model=List[Category])
def list_categories(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(True, description="是否只获取已启用的分类"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取所有分类
    """
    categories = CategoryService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        search=search
    )
    return categories


@router.get("/{category_id}", response_model=Category)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取特定分类
    """
    category = CategoryService.get_by_id(db=db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    return category 