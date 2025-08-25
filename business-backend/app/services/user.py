from typing import Optional, Dict, Any
import httpx
import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import create_access_token

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    async def wechat_login(db: Session, code: str, user_info: Optional[Dict[str, Any]] = None):
        """
        微信小程序登录
        """
        try:
            # 请求微信API获取session_key和openid
            url = f"{settings.WECHAT_API_BASE_URL}/sns/jscode2session"
            params = {
                "appid": settings.WECHAT_APP_ID,
                "secret": settings.WECHAT_APP_SECRET,
                "js_code": code,
                "grant_type": "authorization_code"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response_data = response.json()
            
            # 检查微信API返回
            if "errcode" in response_data and response_data["errcode"] != 0:
                error_msg = f"微信登录失败: {response_data.get('errmsg', '未知错误')}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            openid = response_data.get("openid")
            unionid = response_data.get("unionid")
            session_key = response_data.get("session_key")
            
            if not openid:
                raise ValueError("微信API未返回openid")
            
            # 查找或创建用户
            user = db.query(User).filter(User.openid == openid).first()
            
            if not user:
                # 创建新用户
                user_in = UserCreate(
                    openid=openid,
                    unionid=unionid
                )
                user = User(
                    openid=user_in.openid,
                    unionid=user_in.unionid,
                    credits=settings.DEFAULT_CREDITS
                )
                
                # 如果前端提供了用户信息，则在创建时设置
                if user_info:
                    user.nickname = user_info.get("nickName")
                    user.avatar_url = user_info.get("avatarUrl")
                    user.gender = user_info.get("gender")
                    user.country = user_info.get("country")
                    user.province = user_info.get("province")
                    user.city = user_info.get("city")
                
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # 如果前端提供了用户信息，则更新用户信息
                if user_info:
                    user_update = UserUpdate(
                        nickname=user_info.get("nickName"),
                        avatar_url=user_info.get("avatarUrl"),
                        gender=user_info.get("gender"),
                        country=user_info.get("country"),
                        province=user_info.get("province"),
                        city=user_info.get("city")
                    )
                    
                    has_updates = False
                    for key, value in user_update.dict(exclude_unset=True).items():
                        if value is not None:  # 只更新非空字段
                            setattr(user, key, value)
                            has_updates = True
                    
                    if has_updates:
                        db.commit()
                        db.refresh(user)
            
            # 更新登录时间
            user.last_login_time = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            # 生成访问令牌
            access_token = create_access_token(subject=user.id)
            
            # 计算作品数和被点赞数
            artworks_count = len(user.artworks) if hasattr(user, 'artworks') else 0
            likes_count = sum(1 for artwork in user.artworks for _ in artwork.likes) if hasattr(user, 'artworks') else 0
            
            # 添加额外字段到用户信息
            user_data = {
                "id": user.id,
                "openid": user.openid,
                "unionid": user.unionid,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "gender": user.gender,
                "country": user.country,
                "province": user.province,
                "city": user.city,
                "credits": user.credits,
                "is_blocked": user.is_blocked,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login_time": user.last_login_time,
                "artworks_count": artworks_count,
                "likes_count": likes_count
            }
            
            return {
                "access_token": access_token,
                "user": user_data
            }
            
        except Exception as e:
            logger.error(f"微信登录处理错误: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, user_id: int):
        """
        通过ID获取用户
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def update(db: Session, user_id: int, user_update: UserUpdate):
        """
        更新用户信息
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user 