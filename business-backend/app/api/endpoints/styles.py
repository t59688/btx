from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.style import Style, StyleCreate, StyleUpdate
from app.services.style import StyleService
from app.core.deps import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[Style])
def list_styles(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(True, description="是否只获取已启用的风格"),
    category: Optional[str] = Query(None, description="风格分类"),
    category_id: Optional[int] = Query(None, description="风格分类ID"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取所有风格
    """
    styles = StyleService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        category=category,
        category_id=category_id,
        search=search
    )
    return styles


@router.get("/{style_id}", response_model=Style)
def get_style(
    style_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取特定风格
    """
    style = StyleService.get_by_id(db=db, style_id=style_id)
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风格不存在"
        )
    return style


# 以下为管理员接口，实际项目中应添加管理员权限检查

# @router.post("/", response_model=Style)
# def create_style(
#     style_create: StyleCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ) -> Any:
#     """
#     创建新风格（管理员）
#     """
#     # TODO: 添加管理员权限检查
#     style = StyleService.create(db=db, style_create=style_create)
#     return style


# @router.put("/{style_id}", response_model=Style)
# def update_style(
#     style_id: int,
#     style_update: StyleUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ) -> Any:
#     """
#     更新风格（管理员）
#     """
#     # TODO: 添加管理员权限检查
#     style = StyleService.update(db=db, style_id=style_id, style_update=style_update)
#     if not style:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="风格不存在"
#         )
#     return style


# @router.delete("/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_style(
#     style_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ) -> None:
#     """
#     删除风格（管理员）
#     """
#     # TODO: 添加管理员权限检查
#     success = StyleService.delete(db=db, style_id=style_id)
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="风格不存在"
#         ) 