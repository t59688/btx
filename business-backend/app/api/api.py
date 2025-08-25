from fastapi import APIRouter

from app.api.endpoints import auth, users, artworks, styles, likes, credits, admin, categories, card_keys, products, orders

api_router = APIRouter()


# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户相关路由
api_router.include_router(users.router, prefix="/users", tags=["用户"])

# 作品相关路由
api_router.include_router(artworks.router, prefix="/artworks", tags=["作品"])

# 风格相关路由
api_router.include_router(styles.router, prefix="/styles", tags=["风格"])

# 风格分类路由
api_router.include_router(categories.router, prefix="/categories", tags=["分类"])

# 积分相关路由
api_router.include_router(credits.router, prefix="/credits", tags=["积分"])

# 点赞相关路由
api_router.include_router(likes.router, prefix="/likes", tags=["点赞"])

# 卡密相关路由
api_router.include_router(card_keys.router, prefix="/card-keys", tags=["卡密"])

# 商品相关路由
api_router.include_router(products.router, prefix="/products", tags=["商品"])

# 订单相关路由
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])

# 管理员相关路由
api_router.include_router(admin.router, prefix="/super", tags=["管理后台"]) 