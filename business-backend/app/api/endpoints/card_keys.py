from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.card_key import CardKeyActivate
from app.services.card_key import CardKeyService
from app.core.deps import get_current_active_user

router = APIRouter()

@router.post("/activate", response_model=Dict[str, Any])
def activate_card_key(
    card_key_in: CardKeyActivate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    用户激活卡密
    """
    success, result = CardKeyService.activate(
        db=db,
        card_key_str=card_key_in.card_key,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "激活卡密失败")
        )
    
    return {
        "credits": result["credits"],
        "balance": result["balance"],
        "message": "卡密激活成功"
    } 