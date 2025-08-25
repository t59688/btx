from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import WechatLoginRequest, WechatLoginResponse
from app.services.user import UserService

router = APIRouter()


@router.get("/hello", response_model=Token)
def hello_world() -> Any:
    """
    返回hello world字符串
    """
    return {"access_token": "hello world", "token_type": "bearer"}


@router.post("/wechat/login", response_model=WechatLoginResponse)
async def wechat_login(
    request: WechatLoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    微信小程序登录
    """
    try:
        # 验证code必须存在
        if not request.code:
            raise ValueError("请提供有效的登录code")
            
        # 调用微信登录服务
        result = await UserService.wechat_login(
            db=db,
            code=request.code,
            user_info=request.user_info
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # 记录详细错误信息
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        ) 