from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.order import Order as OrderModel
from app.schemas.order import CreatePaymentRequest, Order, OrderDetail, PaymentCallbackRequest
from app.services.order import OrderService
from app.core.deps import get_current_active_user, get_current_admin_user
from app.tasks import add_order_to_check_queue
from app.core.config import settings

router = APIRouter()


@router.post("/create", response_model=Dict[str, Any])
async def create_order(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    创建订单
    """
    success, result = OrderService.create_order(
        db=db,
        user_id=current_user.id,
        product_id=request.product_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "创建订单失败")
        )
    
    order = result["order"]
    
    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "amount": order.amount,
        "credits": order.credits,
        "message": "订单创建成功"
    }


@router.post("/pay/{order_id}", response_model=Dict[str, Any])
async def pay_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    支付订单
    """
    # 查询订单
    order_detail = OrderService.get_order_detail(db=db, order_id=order_id, user_id=current_user.id)
    if not order_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 创建支付
    success, result = await OrderService.create_payment(
        order_no=order_detail["order_no"],
        amount=order_detail["amount"],
        openid=current_user.openid
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "创建支付失败")
        )
    
    # 将订单添加到检查队列
    add_order_to_check_queue(order_id)
    
    return {
        "payment_data": result["payment_data"],
        "message": "创建支付成功"
    }


@router.post("/callback", response_model=Dict[str, Any])
async def payment_callback(
    request: PaymentCallbackRequest,
    db: Session = Depends(get_db),
    x_payment_token: str = Header(None)
) -> Dict[str, Any]:
    """
    支付回调接口
    """
    print(f"x_payment_token: {x_payment_token}")
    print(f"settings.PAYMENT_CALLBACK_TOKEN: {settings.PAYMENT_CALLBACK_TOKEN}")
    # 验证支付回调token
    if not x_payment_token or x_payment_token != settings.PAYMENT_CALLBACK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的支付回调Token"
        )
    
    success, result = OrderService.process_payment_callback(
        db=db,
        order_no=request.order_no,
        payment_id=request.payment_id,
        status=request.status
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "处理支付回调失败")
        )
    
    return {
        "message": result.get("message", "处理支付回调成功")
    }


@router.get("", response_model=List[Order])
async def get_orders(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Order]:
    """
    获取用户订单列表
    """
    orders = OrderService.get_user_orders(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return orders


@router.get("/{order_id}", response_model=Dict[str, Any])
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取订单详情
    """
    order_detail = OrderService.get_order_detail(
        db=db,
        order_id=order_id,
        user_id=current_user.id
    )
    
    if order_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    return order_detail


@router.get("/payment-status/{order_id}", response_model=Dict[str, Any])
async def check_payment_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    查询支付状态
    """
    # 验证订单属于当前用户
    order = db.query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 查询支付状态
    success, result = await OrderService.query_payment_status(db=db, order_id=order_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "查询支付状态失败")
        )
    
    return result 