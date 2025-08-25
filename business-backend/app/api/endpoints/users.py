from typing import Any, List, Optional
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate
from app.services.user import UserService
from app.core.deps import get_current_active_user, get_current_user, get_optional_current_user
from utils.cos_handler import cos_handler

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取当前用户信息
    """
    return current_user


@router.patch("/me", response_model=UserSchema)
def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    更新当前用户信息
    """
    user = UserService.update(db=db, user_id=current_user.id, user_update=user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.post("/upload-avatar")
async def upload_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Any:
    """
    上传用户头像到腾讯COS并返回永久链接
    """
    try:
        # 检查文件类型
        content_type = avatar.content_type
        if not content_type or not content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只允许上传图片文件"
            )
        
        # 读取文件内容
        contents = await avatar.read()
        
        # 创建临时文件保存头像
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(avatar.filename)[1]) as temp_file:
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        try:
            # 生成对象存储路径
            user_id = current_user.id if current_user else f"temp_{uuid.uuid4().hex[:8]}"
            timestamp = int(os.path.getmtime(temp_file_path))
            file_ext = os.path.splitext(avatar.filename)[1].lower()
            object_key = f"user-avatars/{user_id}_{timestamp}{file_ext}"
            
            # 上传到腾讯云COS
            avatar_url = cos_handler.upload_file(temp_file_path, object_key)
            
            # 如果用户已登录，更新用户的头像URL
            if current_user:
                UserService.update(
                    db=db, 
                    user_id=current_user.id, 
                    user_update=UserUpdate(avatar_url=avatar_url)
                )
            
            # 返回永久头像URL
            return {"avatar_url": avatar_url}
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        # 记录详细错误信息
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传头像失败: {str(e)}"
        ) 