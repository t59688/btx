from typing import List, Optional, Dict, Any, Tuple
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, exists
from sqlalchemy.exc import IntegrityError

from app.models.like import Like
from app.models.artwork import Artwork

logger = logging.getLogger(__name__)


class LikeService:
    @staticmethod
    def like_artwork(
        db: Session, 
        user_id: int, 
        artwork_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        点赞作品
        """
        try:
            # 检查作品是否存在
            artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
            if not artwork:
                return False, {"error": "作品不存在"}
            
            # 创建点赞记录
            like = Like(
                user_id=user_id,
                artwork_id=artwork_id
            )
            db.add(like)
            
            # 更新作品点赞数
            artwork.likes_count += 1
            
            # 提交事务
            db.commit()
            
            return True, {"message": "点赞成功", "likes_count": artwork.likes_count}
            
        except IntegrityError:
            # 唯一约束冲突，用户已经点赞过该作品
            db.rollback()
            return False, {"error": "已经点赞过该作品"}
            
        except Exception as e:
            db.rollback()
            logger.error(f"点赞作品时发生错误: {str(e)}")
            return False, {"error": f"点赞失败: {str(e)}"}
    
    @staticmethod
    def unlike_artwork(
        db: Session, 
        user_id: int, 
        artwork_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        取消点赞作品
        """
        try:
            # 检查作品是否存在
            artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
            if not artwork:
                return False, {"error": "作品不存在"}
            
            # 查找并删除点赞记录
            like = db.query(Like).filter(
                Like.user_id == user_id,
                Like.artwork_id == artwork_id
            ).first()
            
            if not like:
                return False, {"error": "未点赞过该作品"}
            
            db.delete(like)
            
            # 更新作品点赞数（确保不会小于0）
            if artwork.likes_count > 0:
                artwork.likes_count -= 1
            
            # 提交事务
            db.commit()
            
            return True, {"message": "取消点赞成功", "likes_count": artwork.likes_count}
            
        except Exception as e:
            db.rollback()
            logger.error(f"取消点赞作品时发生错误: {str(e)}")
            return False, {"error": f"取消点赞失败: {str(e)}"}
    
    @staticmethod
    def check_user_liked(
        db: Session, 
        user_id: int, 
        artwork_id: int
    ) -> bool:
        """
        检查用户是否已点赞作品
        """
        return db.query(
            exists().where(
                Like.user_id == user_id,
                Like.artwork_id == artwork_id
            )
        ).scalar()
    
    @staticmethod
    def get_user_likes(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Like]:
        """
        获取用户的所有点赞
        """
        return db.query(Like)\
            .filter(Like.user_id == user_id)\
            .order_by(desc(Like.created_at))\
            .offset(skip).limit(limit).all()
    
    @staticmethod
    def get_artwork_likes(
        db: Session, 
        artwork_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Like]:
        """
        获取作品的所有点赞
        """
        return db.query(Like)\
            .filter(Like.artwork_id == artwork_id)\
            .order_by(desc(Like.created_at))\
            .offset(skip).limit(limit).all()
    
    @staticmethod
    def count_user_likes(db: Session, user_id: int) -> int:
        """
        计算用户点赞的总数
        """
        return db.query(func.count(Like.id))\
            .filter(Like.user_id == user_id)\
            .scalar()
    
    @staticmethod
    def count_artwork_likes(db: Session, artwork_id: int) -> int:
        """
        计算作品获得的点赞总数
        """
        return db.query(func.count(Like.id))\
            .filter(Like.artwork_id == artwork_id)\
            .scalar() 