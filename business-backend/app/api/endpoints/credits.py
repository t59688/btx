from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.credit import CreditRecord, AdRewardRequest, UpdateCreditsRequest
from app.services.credit import CreditService
from app.core.deps import get_current_active_user

router = APIRouter()


@router.get("/balance", response_model=Dict[str, int])
async def get_credits_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, int]:
    """
    获取用户积分余额
    """
    balance = CreditService.get_user_credit_balance(db=db, user_id=current_user.id)
    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"balance": balance}


@router.get("/records", response_model=List[CreditRecord])
async def get_credit_records(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[CreditRecord]:
    """
    获取用户积分记录
    """
    records = CreditService.get_user_credit_records(
        db=db, 
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return records


@router.post("/ad-reward", response_model=Dict[str, Any])
async def reward_from_ad(
    request: AdRewardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    从广告获取积分奖励
    """
    success, result = CreditService.ad_reward(
        db=db,
        user_id=current_user.id,
        ad_type=request.ad_type
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "奖励积分失败")
        )
    
    return {
        "reward_amount": result["reward_amount"],
        "balance": result["balance"],
        "message": "奖励积分成功"
    }


# 管理员接口，用于管理用户积分
@router.post("/admin/update", response_model=Dict[str, Any])
async def admin_update_credits(
    user_id: int,
    request: UpdateCreditsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    管理员更新用户积分（管理员）
    """
    # TODO: 添加管理员权限检查
    
    success, result = CreditService.update_credits(
        db=db,
        user_id=user_id,
        amount=request.amount,
        type=request.type,
        description=request.description,
        related_id=request.related_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "更新积分失败")
        )
    
    return {
        "amount": request.amount,
        "balance": result["balance"],
        "message": "更新积分成功"
    } 