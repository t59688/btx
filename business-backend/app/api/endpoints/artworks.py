import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.artwork import Artwork as ArtworkModel
from app.models.like import Like
from app.schemas.artwork import (
    Artwork, CreateArtworkRequest, ArtworkUpdate, ArtworkListParams, ArtworkStatus,
    PublishArtworkRequest
)
from app.services.artwork import ArtworkService
from app.core.deps import get_current_active_user, get_optional_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=Artwork)
async def create_artwork(
    request: CreateArtworkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建新作品
    """
    success, result = await ArtworkService.create(
        db=db,
        user_id=current_user.id,
        style_id=request.style_id,
        image_base64=request.image_base64,
        image_url=request.image_url
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "创建作品失败")
        )
    
    return result["artwork"]


@router.get("", response_model=List[Artwork])
async def list_artworks(
    skip: int = 0,
    limit: int = 10,
    status: Optional[ArtworkStatus] = None,
    is_public: Optional[bool] = Query(None, description="是否公开，None表示全部"),
    style_id: Optional[int] = Query(None, description="风格ID筛选"),
    order_by: str = Query("created_at", description="排序字段: created_at, likes_count, views_count"),
    order_desc: bool = Query(True, description="是否降序排序"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
) -> Any:
    """
    获取作品列表，只返回当前用户自己的作品
    - 可以按公开状态(is_public)筛选
    - 可以按风格(style_id)筛选
    - 可以按状态(status)筛选
    """
    # 构建查询参数
    params = ArtworkListParams(
        skip=skip,
        limit=limit,
        status=status,
        is_public=is_public,
        user_id=current_user.id,  # 始终只查询当前用户的作品
        style_id=style_id,
        order_by=order_by,
        order_desc=order_desc
    )
    
    artworks_db = ArtworkService.get_all(db=db, params=params)
    
    # 处理点赞状态
    artworks_response = []
    liked_artwork_ids = set()
    if current_user: # 检查用户是否登录
        artwork_ids = [art.id for art in artworks_db]
        if artwork_ids:
            likes = db.query(Like.artwork_id).filter(
                Like.user_id == current_user.id, 
                Like.artwork_id.in_(artwork_ids)
            ).all()
            liked_artwork_ids = {like[0] for like in likes}

    for artwork_db in artworks_db:
        artwork_data = Artwork.from_orm(artwork_db).dict() # 使用 from_orm 转换为 Pydantic 模型再转字典
        artwork_data['is_liked_by_current_user'] = artwork_db.id in liked_artwork_ids
        artworks_response.append(Artwork(**artwork_data)) # 重新构造 Pydantic 模型

    return artworks_response


@router.get("/gallery", response_model=List[Artwork])
async def list_gallery_artworks(
    skip: int = 0,
    limit: int = 10,
    style_id: Optional[int] = Query(None, description="风格ID筛选"),
    order_by: str = Query("created_at", description="排序字段: created_at, likes_count, views_count"),
    order_desc: bool = Query(True, description="是否降序排序"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    获取公开画廊的作品
    """
    # 构建查询参数
    params = ArtworkListParams(
        skip=skip,
        limit=limit,
        status=ArtworkStatus.COMPLETED,  # 只查询已完成的作品
        is_public=True,  # 只查询公开的作品
        style_id=style_id,
        order_by=order_by,
        order_desc=order_desc
    )
    
    artworks_db = ArtworkService.get_all(db=db, params=params)
    
    # 处理点赞状态
    artworks_response = []
    liked_artwork_ids = set()
    if current_user: # 检查用户是否登录
        artwork_ids = [art.id for art in artworks_db]
        if artwork_ids:
            likes = db.query(Like.artwork_id).filter(
                Like.user_id == current_user.id, 
                Like.artwork_id.in_(artwork_ids)
            ).all()
            liked_artwork_ids = {like[0] for like in likes}

    for artwork_db in artworks_db:
        artwork_data = Artwork.from_orm(artwork_db).dict() # 使用 from_orm 转换为 Pydantic 模型再转字典
        
        # 根据 public_scope 决定是否包含 source_image_url
        if artwork_db.public_scope == 'result_only':
            artwork_data['source_image_url'] = None # 设置为 None 或删除
            # 或者 del artwork_data['source_image_url'] # 如果希望完全移除字段

        artwork_data['is_liked_by_current_user'] = artwork_db.id in liked_artwork_ids
        artworks_response.append(Artwork(**artwork_data)) # 重新构造 Pydantic 模型

    return artworks_response


@router.get("/user/{user_id}", response_model=List[Artwork])
async def list_user_public_artworks(
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    style_id: Optional[int] = Query(None, description="风格ID筛选"),
    order_by: str = Query("created_at", description="排序字段: created_at, likes_count, views_count"),
    order_desc: bool = Query(True, description="是否降序排序"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
) -> Any:
    """
    获取指定用户的公开作品
    """
    # 构建查询参数
    params = ArtworkListParams(
        skip=skip,
        limit=limit,
        status=ArtworkStatus.COMPLETED,  # 只查询已完成的作品
        is_public=True,  # 只查询公开的作品
        user_id=user_id,
        style_id=style_id,
        order_by=order_by,
        order_desc=order_desc
    )
    
    artworks_db = ArtworkService.get_all(db=db, params=params)
    
    # 处理点赞状态
    artworks_response = []
    liked_artwork_ids = set()
    if current_user: # 检查用户是否登录
        artwork_ids = [art.id for art in artworks_db]
        if artwork_ids:
            likes = db.query(Like.artwork_id).filter(
                Like.user_id == current_user.id, 
                Like.artwork_id.in_(artwork_ids)
            ).all()
            liked_artwork_ids = {like[0] for like in likes}

    for artwork_db in artworks_db:
        artwork_data = Artwork.from_orm(artwork_db).dict() # 使用 from_orm 转换为 Pydantic 模型再转字典
        artwork_data['is_liked_by_current_user'] = artwork_db.id in liked_artwork_ids
        artworks_response.append(Artwork(**artwork_data)) # 重新构造 Pydantic 模型

    return artworks_response


@router.get("/{artwork_id}", response_model=Artwork)
async def get_artwork(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
) -> Any:
    """
    获取特定作品
    """
    artwork_db = ArtworkService.get_by_id(db=db, artwork_id=artwork_id)
    if not artwork_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    
    # 检查权限：非公开作品只能被作者查看
    # 注意：这里允许匿名用户查看公开作品，也允许作者查看自己未公开的作品
    is_owner = current_user and artwork_db.user_id == current_user.id
    if not artwork_db.is_public and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此作品"
        )
    
    # 增加查看次数（如果是公开作品且不是作者本人查看）
    if artwork_db.is_public and not is_owner:
        ArtworkService.increment_view_count(db=db, artwork_id=artwork_id)
    
    # 处理点赞状态
    is_liked = False
    if current_user:
        like = db.query(Like).filter(
            Like.user_id == current_user.id,
            Like.artwork_id == artwork_id
        ).first()
        is_liked = like is not None

    # 使用 Pydantic 模型转换并设置点赞状态
    artwork_response = Artwork.from_orm(artwork_db)
    artwork_response.is_liked_by_current_user = is_liked
    
    return artwork_response


@router.patch("/{artwork_id}/publish", response_model=Artwork)
async def publish_artwork(
    artwork_id: int,
    request: PublishArtworkRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    发布或设为私密作品
    """
    # 先获取作品
    artwork = ArtworkService.get_by_id(db=db, artwork_id=artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    
    # 检查权限：只能由作者操作
    if artwork.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此作品"
        )
    
    # 更新公开状态和范围
    updated_artwork = ArtworkService.update_publish_settings(
        db=db, 
        artwork_id=artwork_id, 
        is_public=request.is_public,
        public_scope=request.public_scope
    )
    
    if not updated_artwork:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败，请确保作品已完成"
        )
    
    # 处理点赞状态 (因为返回的是 Artwork 模型，需要这个字段)
    is_liked = False
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.artwork_id == artwork_id
    ).first()
    is_liked = like is not None
    updated_artwork.is_liked_by_current_user = is_liked

    return updated_artwork


@router.delete("/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artwork(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """
    删除作品
    """
    # 先获取作品
    artwork = ArtworkService.get_by_id(db=db, artwork_id=artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    
    # 检查权限：只能由作者操作
    if artwork.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此作品"
        )
    
    # 删除作品
    success = ArtworkService.delete(db=db, artwork_id=artwork_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除失败"
        )
    
    # 状态码为204的路由不应返回任何内容


@router.get("/{artwork_id}/progress")
async def get_artwork_progress(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取作品处理进度
    """
    # 先获取作品
    artwork = ArtworkService.get_by_id(db=db, artwork_id=artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    
    # 检查权限：只能由作者查看进度
    if artwork.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此作品进度"
        )
    
    # 获取作品进度
    result = ArtworkService.get_artwork_progress(db=db, artwork_id=artwork_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "获取进度失败")
        )
    
    return result


@router.post("/{artwork_id}/view", status_code=status.HTTP_200_OK)
async def increment_artwork_view(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
) -> Any:
    """
    增加作品的访问次数
    """
    artwork_db = ArtworkService.get_by_id(db=db, artwork_id=artwork_id)
    if not artwork_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    
    # 检查权限：非公开作品只能被作者查看
    is_owner = current_user and artwork_db.user_id == current_user.id
    if not artwork_db.is_public and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此作品"
        )
    
    # 增加查看次数（如果不是作者本人查看）
    if not is_owner:
        updated_artwork = ArtworkService.increment_view_count(db=db, artwork_id=artwork_id)
        if not updated_artwork:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新访问次数失败"
            )
    else:
        logger.info("作者本人查看作品，不增加访问次数")
    
    return {"success": True, "views_count": artwork_db.views_count + (0 if is_owner else 1)} 