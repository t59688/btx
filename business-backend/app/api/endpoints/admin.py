from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import timedelta, datetime
from pydantic import BaseModel
import tempfile
import os
import uuid
import httpx
from decimal import Decimal, ROUND_HALF_UP

from app.core.config import settings
from app.db.session import get_db
from app.models.admin import Admin
from app.models.user import User
from app.models.system_config import SystemConfig
from app.schemas.admin import Admin as AdminSchema, AdminCreate, AdminUpdate, AdminLogin, AdminLoginResponse
from app.schemas.user import User as UserSchema, UserUpdate
from app.schemas.style import Style as StyleSchema, StyleCreate, StyleUpdate
from app.schemas.artwork import Artwork as ArtworkSchema, ArtworkStatus, ArtworkUpdate, ArtworkListParams
from app.schemas.credit import UpdateCreditsRequest, CreditRecordType, CreditRecord as CreditRecordSchema
from app.schemas.category import Category as CategorySchema, CategoryCreate, CategoryUpdate
from app.services.admin import AdminService
from app.services.user import UserService
from app.services.style import StyleService
from app.services.artwork import ArtworkService
from app.services.credit import CreditService
from app.services.system_config import SystemConfigService
from app.services.category import CategoryService
from utils.cos_handler import cos_handler
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

# 系统配置更新请求模型
class ConfigUpdateRequest(BaseModel):
    value: str
    description: Optional[str] = None

# 系统配置创建请求模型
class ConfigCreateRequest(BaseModel):
    config_key: str
    value: str
    description: Optional[str] = None

# 用户封禁/解封请求模型
class BlockUserRequest(BaseModel):
    is_blocked: bool

# 分页响应模型
class PageResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int

# 积分记录分页响应模型
class CreditRecordPageResponse(PageResponse):
    items: List[CreditRecordSchema]

router = APIRouter()

# 管理员认证和管理
@router.post("/login", response_model=AdminLoginResponse)
async def login_admin(
    form_data: AdminLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    管理员登录
    """
    admin = AdminService.authenticate_admin(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新登录时间
    AdminService.update_admin_login_time(db, admin.id)
    
    # 生成访问令牌
    access_token = AdminService.create_access_token(data={"sub": str(admin.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": admin
    }


@router.get("/me", response_model=AdminSchema)
async def read_admin_me(
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取当前管理员信息
    """
    return current_admin


@router.get("/admins", response_model=List[AdminSchema])
async def read_admins(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取所有管理员
    """
    admins = AdminService.get_admins(db, skip=skip, limit=limit)
    return admins


@router.post("/admins", response_model=AdminSchema)
async def create_admin(
    admin_in: AdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    创建新管理员
    """
    # 检查用户名是否已存在
    if AdminService.get_admin_by_username(db, admin_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    admin = AdminService.create_admin(db, admin_in)
    return admin


@router.put("/admins/{admin_id}", response_model=AdminSchema)
async def update_admin(
    admin_id: int,
    admin_in: AdminUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新管理员信息
    """
    admin = AdminService.get_admin(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )
    
    admin = AdminService.update_admin(db, admin_id, admin_in)
    return admin


@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除管理员
    """
    # 不允许删除自己
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录的管理员"
        )
    
    admin = AdminService.get_admin(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )
    
    AdminService.delete_admin(db, admin_id)


# 用户管理
@router.get("/users", response_model=List[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    nickname: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取用户列表（支持筛选）
    """
    # 这里需要在UserService中添加一个获取用户列表的方法，支持筛选
    # 由于示例代码中没有提供此方法，这里简单返回所有用户
    users = db.query(User)
    
    if nickname:
        users = users.filter(User.nickname.like(f"%{nickname}%"))
    
    if is_blocked is not None:
        users = users.filter(User.is_blocked == is_blocked)
    
    users = users.offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取特定用户
    """
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/users/{user_id}/block", response_model=UserSchema)
async def block_user(
    user_id: int,
    block_data: BlockUserRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    封禁/解封用户
    
    请求体:
    - is_blocked: 布尔值，true表示封禁，false表示解封
    """
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.is_blocked = block_data.is_blocked
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/credits", response_model=Dict[str, Any])
async def update_user_credits(
    user_id: int,
    request: UpdateCreditsRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    调整用户积分
    """
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    success, result = CreditService.update_credits(
        db=db,
        user_id=user_id,
        amount=request.amount,
        type=request.type,
        description=request.description or f"管理员调整积分: {request.amount}",
        related_id=request.related_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "积分调整失败")
        )
    
    return {
        "amount": request.amount,
        "balance": result["balance"],
        "message": "积分调整成功"
    }


@router.get("/users/{user_id}/credit-records", response_model=CreditRecordPageResponse)
async def read_user_credit_records(
    user_id: int,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    per_page: int = Query(10, ge=1, le=100, description="每页记录数"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取用户的积分记录
    
    参数:
    - user_id: 用户ID
    - page: 页码，从1开始
    - per_page: 每页记录数，默认10
    
    返回:
    - 分页的积分记录列表
    """
    # 检查用户是否存在
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 计算跳过的记录数
    skip = (page - 1) * per_page
    
    # 获取积分记录
    records = CreditService.get_user_credit_records(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=per_page
    )
    
    # 获取记录总数
    total = CreditService.count_user_credit_records(db, user_id)
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "items": records,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


# 风格管理
@router.get("/styles", response_model=List[StyleSchema])
async def read_styles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    category: Optional[str] = None, 
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取风格列表
    """
    skip = (page - 1) * limit
    
    styles = StyleService.get_all(
        db=db, 
        skip=skip, 
        limit=limit,
        is_active=is_active,
        category=category,
        search=name if name else None
    )
    
    return styles

@router.post("/styles", response_model=StyleSchema)
async def create_style(
    style_in: StyleCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    创建新风格
    """
    style = StyleService.create(db, style_in)
    return style


@router.put("/styles/{style_id}", response_model=StyleSchema)
async def update_style(
    style_id: int,
    style_in: StyleUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新风格
    """
    style = StyleService.get_by_id(db, style_id)
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风格不存在"
        )
    
    style = StyleService.update(db, style_id, style_in)
    return style


@router.delete("/styles/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style(
    style_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除风格
    """
    style = StyleService.get_by_id(db, style_id)
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风格不存在"
        )
    
    # 检查是否有关联作品
    artwork_count = db.query(ArtworkService.count(db, style_id=style_id)).scalar()
    if artwork_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该风格已被使用，无法删除。关联作品数：{artwork_count}"
        )
    
    StyleService.delete(db, style_id)


# 作品管理
@router.get("/artworks", response_model=List[ArtworkSchema])
async def read_artworks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    is_public: Optional[bool] = None,
    user_id: Optional[int] = None,
    style_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取作品列表
    
    参数:
    - page: 页码，从1开始
    - limit: 每页数量，默认20
    - status: 状态筛选，可选值: processing, completed, failed
    - is_public: 是否公开
    - user_id: 用户ID
    - style_id: 风格ID
    """
    skip = (page - 1) * limit
    
    # 处理空字符串的情况
    status_value = None
    if status and status.strip():
        # 只有当status有值且不为空字符串时才使用它
        try:
            status_value = ArtworkStatus(status).value
        except ValueError:
            # 无效的状态值，忽略
            pass
    
    params = ArtworkListParams(
        skip=skip,
        limit=limit,
        status=status_value,
        is_public=is_public,
        user_id=user_id,
        style_id=style_id,
        order_by="created_at",
        order_desc=True
    )
    
    artworks = ArtworkService.get_all(db, params)
    return artworks


@router.get("/artworks/{artwork_id}", response_model=ArtworkSchema)
async def read_artwork(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取特定作品
    """
    artwork = ArtworkService.get_by_id(db, artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    return artwork


@router.put("/artworks/{artwork_id}", response_model=ArtworkSchema)
async def update_artwork_status(
    artwork_id: int,
    artwork_in: ArtworkUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新作品状态
    """
    artwork = ArtworkService.get_by_id(db, artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    
    artwork = ArtworkService.update(db, artwork_id, artwork_in)
    return artwork


@router.delete("/artworks/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artwork(
    artwork_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除作品
    """
    artwork = ArtworkService.get_by_id(db, artwork_id)
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作品不存在"
        )
    
    success = ArtworkService.delete(db, artwork_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除作品失败"
        )




# 系统配置管理
@router.post("/configs", response_model=Dict[str, Any])
async def create_system_config(
    request_data: ConfigCreateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    创建新系统配置
    """
    # 检查配置是否已存在
    existing_config = db.query(SystemConfig).filter(SystemConfig.config_key == request_data.config_key).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配置 '{request_data.config_key}' 已存在"
        )
    
    # 使用服务创建配置，它会同时更新内存中的配置
    config = SystemConfigService.set_config(
        db, 
        request_data.config_key, 
        request_data.value,
        request_data.description
    )
    
    return {
        "key": config.config_key, 
        "value": config.config_value,
        "description": config.description
    }

@router.get("/configs", response_model=Dict[str, Dict[str, str]])
async def get_system_configs(
    prefix: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取系统配置
    """
    configs = SystemConfigService.get_config_map(db, prefix)
    return configs


@router.put("/configs/{config_key}", response_model=Dict[str, Any])
async def update_system_config(
    config_key: str,
    request_data: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新系统配置
    """
    # 使用服务更新配置，它会同时更新内存中的配置
    config = SystemConfigService.set_config(db, config_key, request_data.value, request_data.description)
    return {
        "key": config.config_key, 
        "value": config.config_value,
        "description": config.description
    }


@router.delete("/configs/{config_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system_config(
    config_key: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除系统配置
    """
    # 使用服务删除配置，它会同时从内存中删除配置
    success = SystemConfigService.delete_config(db, config_key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )


# 数据统计
@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_stats_overview(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取系统概览数据
    """
    # 用户总数
    total_users = db.query(User).count()
    
    # 风格总数
    total_styles = db.query(StyleService.count(db)).scalar()
    
    # 作品总数
    total_artworks = db.query(ArtworkService.count(db)).scalar()
    
    # 今日新增用户
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_users = db.query(User).filter(User.created_at >= today_start).count()
    
    # 今日新增作品
    from app.models.artwork import Artwork
    today_artworks = db.query(Artwork).filter(Artwork.created_at >= today_start).count()
    
    
    # 近7天新增用户数据
    from app.models.artwork import Artwork
    from sqlalchemy import func, cast, Date
    
    days_ago_7 = today - timedelta(days=6)
    
    # 近7天用户注册统计
    user_stats = db.query(
        cast(User.created_at, Date).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= days_ago_7
    ).group_by(
        cast(User.created_at, Date)
    ).all()
    
    user_stats_dict = {(days_ago_7 + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    for date, count in user_stats:
        user_stats_dict[date.isoformat()] = count
    
    # 近7天作品创建统计
    artwork_stats = db.query(
        cast(Artwork.created_at, Date).label('date'),
        func.count(Artwork.id).label('count')
    ).filter(
        Artwork.created_at >= days_ago_7
    ).group_by(
        cast(Artwork.created_at, Date)
    ).all()
    
    artwork_stats_dict = {(days_ago_7 + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    for date, count in artwork_stats:
        artwork_stats_dict[date.isoformat()] = count
    
    return {
        "total_users": total_users,
        "total_styles": total_styles,
        "total_artworks": total_artworks,
        "today_users": today_users,
        "today_artworks": today_artworks,
        "user_stats": user_stats_dict,
        "artwork_stats": artwork_stats_dict
    }


@router.get("/stats/styles", response_model=List[Dict[str, Any]])
async def get_style_usage_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取风格使用情况统计
    """
    from sqlalchemy import func
    from app.models.style import Style
    from app.models.artwork import Artwork
    
    # 查询每个风格及其使用次数
    style_stats = db.query(
        Style.id,
        Style.name,
        Style.category,
        Style.credits_cost,
        func.count(Artwork.id).label('usage_count')
    ).outerjoin(
        Artwork, Style.id == Artwork.style_id
    ).group_by(
        Style.id
    ).order_by(
        func.count(Artwork.id).desc()
    ).all()
    
    result = []
    for id, name, category, credits_cost, usage_count in style_stats:
        result.append({
            "id": id,
            "name": name,
            "category": category,
            "credits_cost": credits_cost,
            "usage_count": usage_count
        })
    
    return result


# 分类管理
@router.get("/categories", response_model=List[CategorySchema])
async def read_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取所有分类
    """
    skip = (page - 1) * limit
    
    if name:
        search = name
    else:
        search = None
    
    categories = CategoryService.get_all(
        db=db, 
        skip=skip, 
        limit=limit, 
        is_active=is_active, 
        search=search
    )
    
    return categories


@router.post("/categories", response_model=CategorySchema)
async def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    创建新分类
    """
    category = CategoryService.create(db, category_in)
    return category


@router.put("/categories/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新分类
    """
    category = CategoryService.get_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    
    category = CategoryService.update(db, category_id, category_in)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除分类
    """
    category = CategoryService.get_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分类不存在"
        )
    
    # 检查分类是否关联风格
    # 如果有关联的风格，则不允许删除
    # 这一步应该在service层实现，但为了简单起见，我们在这里处理
    styles_count = db.query(Style).filter(Style.category_id == category_id).count()
    if styles_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该分类下有{styles_count}个风格，无法删除"
        )
    
    success = CategoryService.delete(db, category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除分类失败"
        )


# 文件上传接口
@router.post("/upload", response_model=Dict[str, str])
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("common"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    上传文件到腾讯云COS并返回URL
    
    - **file**: 要上传的文件
    - **folder**: 存储的文件夹名称，默认为common
    """
    try:
        # 检查文件类型
        content_type = file.content_type
        if not content_type or not content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只允许上传图片文件"
            )
        
        # 读取文件内容
        contents = await file.read()
        
        # 创建临时文件保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        try:
            # 生成对象存储路径
            timestamp = int(datetime.now().timestamp())
            file_ext = os.path.splitext(file.filename)[1].lower()
            random_str = uuid.uuid4().hex[:8]
            object_key = f"styles/{folder}/{timestamp}_{random_str}{file_ext}"
            
            # 上传到腾讯云COS
            file_url = cos_handler.upload_file(temp_file_path, object_key)
            
            # 返回文件URL
            return {"url": file_url}
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文件失败: {str(e)}"
        )

# 卡密管理路由
from app.schemas.card_key import CardKey, CardKeyCreate, CardKeyListParams, CardKeyStatusUpdate, CardKeyBatchCreateResponse, CardKeyListResponse
from app.services.card_key import CardKeyService

@router.post("/card-keys", response_model=CardKeyBatchCreateResponse)
async def create_card_keys(
    card_key_in: CardKeyCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    批量创建卡密
    
    - **credits**: 积分面值
    - **count**: 创建数量，1-1000之间
    - **batch_no**: 批次号，可选
    - **expired_at**: 过期时间，可选
    - **remark**: 备注，可选
    """
    result = CardKeyService.create_batch(db, card_key_in, current_admin.id)
    return result


@router.get("/card-keys", response_model=CardKeyListResponse)
async def read_card_keys(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    per_page: int = Query(10, ge=1, le=100, description="每页记录数"),
    status: Optional[str] = Query(None, description="状态筛选: unused, used, invalid"),
    batch_no: Optional[str] = Query(None, description="批次号筛选"),
    created_start: Optional[datetime] = Query(None, description="创建开始时间"),
    created_end: Optional[datetime] = Query(None, description="创建结束时间"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取卡密列表，支持分页和筛选
    """
    # 计算跳过的记录数
    skip = (page - 1) * per_page
    
    # 构建查询参数
    params = CardKeyListParams(
        skip=skip,
        limit=per_page,
        status=status,
        batch_no=batch_no,
        created_start=created_start,
        created_end=created_end,
        order_by="created_at",
        order_desc=True
    )
    
    # 获取卡密列表
    card_keys = CardKeyService.get_all(db, params)
    
    # 获取总记录数
    total = CardKeyService.count(
        db, 
        status=status,
        batch_no=batch_no
    )
    
    # 计算总页数
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "items": card_keys,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


@router.get("/card-keys/{card_key_id}", response_model=CardKey)
async def read_card_key(
    card_key_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取特定卡密
    """
    card_key = CardKeyService.get_by_id(db, card_key_id)
    if not card_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="卡密不存在"
        )
    return card_key


@router.put("/card-keys/{card_key_id}/status", response_model=CardKey)
async def update_card_key_status(
    card_key_id: int,
    status_in: CardKeyStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新卡密状态
    """
    # 检查卡密是否存在
    card_key = CardKeyService.get_by_id(db, card_key_id)
    if not card_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="卡密不存在"
        )
    
    # 更新状态
    card_key = CardKeyService.update_status(db, card_key_id, status_in.status)
    if not card_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新卡密状态失败"
        )
    
    return card_key


@router.delete("/card-keys/{card_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card_key(
    card_key_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除卡密（仅未使用的可删除）
    """
    # 删除卡密
    success = CardKeyService.delete(db, card_key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除卡密失败，可能已被使用或不存在"
        )


# 商品管理接口
@router.get("/products", response_model=Dict[str, Any])
async def admin_get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取商品列表（管理员）
    
    参数:
    - page: 页码，从1开始
    - limit: 每页数量，默认20
    - is_active: 是否上架筛选
    - search: 商品名称搜索
    """
    skip = (page - 1) * limit
    
    # 获取商品列表
    products = db.query(Product)
    
    # 应用筛选条件
    products = products.filter(Product.is_deleted == False)
    
    if is_active is not None:
        products = products.filter(Product.is_active == is_active)
    
    if search:
        products = products.filter(Product.name.like(f"%{search}%"))
    
    # 按创建时间倒序排序
    products = products.order_by(desc(Product.created_at))
    
    # 计算总数
    total = products.count()
    
    # 应用分页
    products = products.offset(skip).limit(limit).all()
    
    # 构建响应数据
    result = []
    for product in products:
        result.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "credits": product.credits,
            "price": product.price,
            "image_url": product.image_url,
            "is_active": product.is_active,
            "sort_order": product.sort_order,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        })
    
    # 计算总页数
    total_pages = (total + limit - 1) // limit
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": limit,
        "total_pages": total_pages
    }


@router.get("/products/{product_id}", response_model=Dict[str, Any])
async def admin_get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取单个商品详情（管理员）
    """
    from app.services.product import ProductService
    
    product = ProductService.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    return product


@router.post("/products", response_model=Dict[str, Any])
async def admin_create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    创建商品（管理员）
    """
    from app.services.product import ProductService
    
    product = ProductService.create_product(db, product_in)
    return product


@router.put("/products/{product_id}", response_model=Dict[str, Any])
async def admin_update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新商品（管理员）
    """
    from app.services.product import ProductService
    
    product = ProductService.update_product(db, product_id, product_in)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除商品（管理员）
    """
    from app.services.product import ProductService
    
    success = ProductService.delete_product(db, product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )


# 订单管理接口
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderUpdate

class OrderListParams(BaseModel):
    skip: int = 0
    limit: int = 20
    status: Optional[str] = None
    user_id: Optional[int] = None
    order_no: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None


@router.get("/orders", response_model=Dict[str, Any])
async def admin_get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    order_no: Optional[str] = None,
    date_start: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取订单列表（管理员）
    
    参数:
    - page: 页码，从1开始
    - limit: 每页数量，默认20
    - status: 订单状态筛选
    - user_id: 用户ID筛选
    - order_no: 订单号筛选
    - date_start: 创建时间起始
    - date_end: 创建时间结束
    """
    from sqlalchemy import desc
    from app.models.product import Product
    from app.models.user import User
    
    skip = (page - 1) * limit
    
    # 创建联合查询
    orders = db.query(
        Order,
        Product.name.label("product_name"),
        User.nickname.label("user_nickname")
    ).join(
        Product, Order.product_id == Product.id
    ).join(
        User, Order.user_id == User.id
    )
    
    # 应用筛选条件
    orders = orders.filter(Order.is_deleted == False)
    
    if status:
        try:
            orders = orders.filter(Order.status == OrderStatus(status))
        except ValueError:
            # 无效的状态，忽略
            pass
    
    if user_id:
        orders = orders.filter(Order.user_id == user_id)
    
    if order_no:
        orders = orders.filter(Order.order_no.like(f"%{order_no}%"))
    
    if date_start:
        orders = orders.filter(Order.created_at >= date_start)
    
    if date_end:
        orders = orders.filter(Order.created_at <= date_end)
    
    # 计算总数
    total = orders.count()
    
    # 按创建时间倒序排序并分页
    orders = orders.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    # 构建响应数据
    result = []
    for order, product_name, user_nickname in orders:
        result.append({
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "user_nickname": user_nickname,
            "product_id": order.product_id,
            "product_name": product_name,
            "amount": order.amount,
            "credits": order.credits,
            "status": order.status,
            "payment_id": order.payment_id,
            "payment_time": order.payment_time,
            "refund_time": order.refund_time,
            "remark": order.remark,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        })
    
    # 计算总页数
    total_pages = (total + limit - 1) // limit
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": limit,
        "total_pages": total_pages
    }


@router.get("/orders/{order_id}", response_model=Dict[str, Any])
async def admin_get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    获取订单详情（管理员）
    """
    # 联合查询订单、商品和用户信息
    from app.models.product import Product
    from app.models.user import User
    
    result = db.query(
        Order,
        Product.name.label("product_name"),
        Product.description.label("product_description"),
        Product.image_url.label("product_image_url"),
        User.nickname.label("user_nickname"),
        User.avatar_url.label("user_avatar")
    ).join(
        Product, Order.product_id == Product.id
    ).join(
        User, Order.user_id == User.id
    ).filter(
        Order.id == order_id,
        Order.is_deleted == False
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    order, product_name, product_description, product_image_url, user_nickname, user_avatar = result
    
    # 构建响应数据
    order_detail = {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "user_nickname": user_nickname,
        "user_avatar": user_avatar,
        "product_id": order.product_id,
        "product_name": product_name,
        "product_description": product_description,
        "product_image_url": product_image_url,
        "amount": order.amount,
        "credits": order.credits,
        "status": order.status,
        "payment_id": order.payment_id,
        "payment_time": order.payment_time,
        "refund_time": order.refund_time,
        "remark": order.remark,
        "created_at": order.created_at,
        "updated_at": order.updated_at
    }
    
    return order_detail


@router.put("/orders/{order_id}", response_model=Dict[str, Any])
async def admin_update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    更新订单状态（管理员）
    """
    # 查询订单
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.is_deleted == False
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 更新订单状态
    update_data = order_update.dict(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(order, key, value)
    
        db.commit()
        db.refresh(order)
    
    return {
        "id": order.id,
        "order_no": order.order_no,
        "status": order.status,
        "message": "订单更新成功"
    }


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> None:
    """
    删除订单（管理员）
    """
    # 查询订单
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.is_deleted == False
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 软删除订单
    order.is_deleted = True
    db.commit()


# 订单退款接口
@router.post("/orders/{order_id}/refund", response_model=Dict[str, Any])
async def admin_refund_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Any:
    """
    订单退款（管理员）
    """
    from app.services.credit import CreditService
    
    # 查询订单
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.is_deleted == False
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 检查订单状态是否可退款
    if order.status not in [OrderStatus.PAID, OrderStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前订单状态 {order.status} 不可退款"
        )
    
    try:
        # 调用支付网关退款
        refund_url = f"{settings.PAYMENT_GATEWAY_URL}/api/pay/refund" 
        
        refund_data = {
            "outTradeNo": order.order_no,
            "refundAmount": int(order.amount * 100),  # 微信退款金额单位为分
            "refundReason": "管理员发起退款"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(refund_url, json=refund_data)
            result = response.json()
        
        if response.status_code != 200 or result.get("code") != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"调用退款接口失败: {result.get('message', '未知错误')}"
            )
        
        # 更新订单状态为已退款
        order.status = OrderStatus.REFUNDED
        order.refund_time = datetime.now()
        
        # 减去用户积分
        success, credit_result = CreditService.update_credits(
            db=db,
            user_id=order.user_id,
            amount=-order.credits,  # 负数表示减少积分
            type="refund",
            description=f"订单退款，扣除{order.credits}积分",
            related_id=order.id
        )
        
        if not success:
            # 记录错误但不阻止退款流程
            order.remark = f"退款成功但扣除积分失败: {credit_result.get('error')}"
        
        db.commit()
        
        return {
            "order_id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "message": "订单退款成功"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订单退款失败: {str(e)}"
        )


# 商品销售统计接口
@router.get("/statistics/product-sales", response_model=List[Dict[str, Any]])
async def get_product_sales_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> List[Dict[str, Any]]:
    """
    获取商品销售统计数据
    
    返回:
    - 每个商品的销售数量和销售总额
    """
    from sqlalchemy import func
    
    # 查询已完成或已支付的订单中的商品销售情况
    product_sales = db.query(
        Order.product_id,
        Product.name.label("product_name"),
        func.count(Order.id).label("sales_count"),
        func.sum(Order.amount).label("total_amount")
    ).join(
        Product, Order.product_id == Product.id
    ).filter(
        Order.status.in_(["paid", "completed"]),
        Order.is_deleted == False,
        Product.is_deleted == False
    ).group_by(
        Order.product_id,
        Product.name
    ).order_by(
        func.count(Order.id).desc()  # 按销量降序排序
    ).all()
    
    # 构建结果列表
    result = []
    for product_id, product_name, sales_count, total_amount in product_sales:
        # 处理金额精度
        if total_amount is not None:
            # 转换为Decimal并保留2位小数
            decimal_amount = Decimal(str(total_amount)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            formatted_amount = str(decimal_amount)
        else:
            formatted_amount = "0.00"
            
        result.append({
            "productId": product_id,
            "productName": product_name,
            "salesCount": sales_count,
            "totalAmount": formatted_amount
        })
    
    return result


# 统计数据接口
@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(AdminService.get_current_admin),
) -> Dict[str, Any]:
    """
    获取系统数据统计
    
    返回:
    - userCount: 用户总数
    - artworkCount: 作品总数
    - productCount: 商品总数
    - orderCount: 订单总数
    - todayUsers: 今日新增用户
    - todayArtworks: 今日新增作品
    - todayOrders: 今日新增订单
    - userStats: 近7天用户增长统计
    - orderStats: 近7天订单数量统计
    - revenueStats: 近7天收入统计
    """
    from app.models.user import User
    from app.models.artwork import Artwork
    from sqlalchemy import func, cast, Date
    
    # 获取当前日期和7天前的日期
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    days_ago_7 = today - timedelta(days=6)
    
    # 基础统计数据
    user_count = db.query(User).filter(User.is_deleted == False).count()
    artwork_count = db.query(Artwork).filter(Artwork.is_deleted == False).count()
    product_count = db.query(Product).filter(Product.is_deleted == False).count()
    order_count = db.query(Order).filter(Order.is_deleted == False).count()
    
    # 今日新增数据
    today_users = db.query(User).filter(
        User.created_at >= today_start,
        User.is_deleted == False
    ).count()
    
    today_artworks = db.query(Artwork).filter(
        Artwork.created_at >= today_start,
        Artwork.is_deleted == False
    ).count()
    
    today_orders = db.query(Order).filter(
        Order.created_at >= today_start,
        Order.is_deleted == False
    ).count()
    
    # 近7天用户增长统计
    user_stats = db.query(
        cast(User.created_at, Date).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= datetime.combine(days_ago_7, datetime.min.time()),
        User.is_deleted == False
    ).group_by(
        cast(User.created_at, Date)
    ).all()
    
    user_stats_dict = {(days_ago_7 + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    for date, count in user_stats:
        user_stats_dict[date.isoformat()] = count
    
    # 近7天订单数量统计
    order_stats = db.query(
        cast(Order.created_at, Date).label('date'),
        func.count(Order.id).label('count')
    ).filter(
        Order.created_at >= datetime.combine(days_ago_7, datetime.min.time()),
        Order.is_deleted == False
    ).group_by(
        cast(Order.created_at, Date)
    ).all()
    
    order_stats_dict = {(days_ago_7 + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    for date, count in order_stats:
        order_stats_dict[date.isoformat()] = count
    
    # 近7天收入统计
    revenue_stats = db.query(
        cast(Order.created_at, Date).label('date'),
        func.sum(Order.amount).label('revenue')
    ).filter(
        Order.created_at >= datetime.combine(days_ago_7, datetime.min.time()),
        Order.status.in_(["paid", "completed"]),
        Order.is_deleted == False
    ).group_by(
        cast(Order.created_at, Date)
    ).all()
    
    # 初始化所有日期的收入为0.00
    revenue_stats_dict = {(days_ago_7 + timedelta(days=i)).isoformat(): Decimal('0.00') for i in range(7)}
    
    # 使用Decimal处理收入金额，保证2位小数精度
    for date, revenue in revenue_stats:
        if revenue is not None:
            # 转换为Decimal并四舍五入到2位小数
            decimal_revenue = Decimal(str(revenue)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            revenue_stats_dict[date.isoformat()] = decimal_revenue
    
    # 将Decimal对象转换为字符串，确保前端接收到的是格式化的金额字符串
    formatted_revenue_stats = {date: str(amount) for date, amount in revenue_stats_dict.items()}
    
    return {
        "userCount": user_count,
        "artworkCount": artwork_count,
        "productCount": product_count,
        "orderCount": order_count,
        "todayUsers": today_users,
        "todayArtworks": today_artworks,
        "todayOrders": today_orders,
        "userStats": user_stats_dict,
        "orderStats": order_stats_dict,
        "revenueStats": formatted_revenue_stats
    } 