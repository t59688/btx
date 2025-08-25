from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.like import Like
from app.services.like import LikeService
from app.core.deps import get_current_active_user

router = APIRouter()


@router.post("/{artwork_id}")
async def like_artwork(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    点赞作品
    """
    success, result = LikeService.like_artwork(
        db=db, 
        user_id=current_user.id, 
        artwork_id=artwork_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "点赞失败")
        )
    
    return result


@router.delete("/{artwork_id}")
async def unlike_artwork(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    取消点赞作品
    """
    success, result = LikeService.unlike_artwork(
        db=db, 
        user_id=current_user.id, 
        artwork_id=artwork_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "取消点赞失败")
        )
    
    return result


@router.get("/check/{artwork_id}")
async def check_user_liked(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, bool]:
    """
    检查用户是否已点赞作品
    """
    liked = LikeService.check_user_liked(
        db=db, 
        user_id=current_user.id, 
        artwork_id=artwork_id
    )
    
    return {"liked": liked} 