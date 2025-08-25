from typing import List, Optional, Dict, Any, Tuple
import logging
import uuid
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import threading

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.credit import CreditService
from app.core.config import settings

logger = logging.getLogger(__name__)

# 积分处理锁，防止重复处理
credit_processing_locks = {}

class OrderService:
    @staticmethod
    def generate_order_no() -> str:
        """生成唯一订单号"""
        # 使用时间戳和UUID生成唯一订单号
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        # 取UUID的前8位
        unique_id = str(uuid.uuid4()).replace('-', '')[:8]
        return f"P{timestamp}{unique_id}"

    @staticmethod
    def create_order(db: Session, user_id: int, product_id: int) -> Tuple[bool, Dict[str, Any]]:
        """创建订单"""
        try:
            # 查询商品信息
            product = db.query(Product).filter(
                Product.id == product_id,
                Product.is_active == True,
                Product.is_deleted == False
            ).first()
            
            if not product:
                return False, {"error": "商品不存在或已下架"}
            
            # 生成订单号
            order_no = OrderService.generate_order_no()
            
            # 创建订单
            order = Order(
                order_no=order_no,
                user_id=user_id,
                product_id=product_id,
                amount=product.price,
                credits=product.credits,
                status=OrderStatus.PENDING
            )
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            return True, {"order": order}
        except Exception as e:
            db.rollback()
            logger.error(f"创建订单失败: {str(e)}")
            return False, {"error": f"创建订单失败: {str(e)}"}
    
    @staticmethod
    async def create_payment(order_no: str, amount: float, openid: str) -> Tuple[bool, Dict[str, Any]]:
        """调用支付网关创建支付"""
        try:
            # 调用Java支付服务创建支付
            payment_url = f"{settings.PAYMENT_GATEWAY_URL}/api/pay/create-payment"
            
            # 设置过期时间为一分钟后
            expire_time = (datetime.now() + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S+08:00")
            
            payment_data = {
                "outTradeNo": order_no,
                "description": "积分充值",
                "amount": int(amount * 100),  # 微信支付金额单位为分
                "openid": openid,
                "attach": "credits_purchase",
                "timeExpire": expire_time  # 添加过期时间
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(payment_url, json=payment_data)
                result = response.json()
            
            if response.status_code != 200 or result.get("code") != 200:
                return False, {"error": f"创建支付失败: {result.get('message', '未知错误')}"}
            
            return True, {"payment_data": result.get("data")}
        except Exception as e:
            logger.error(f"创建支付请求失败: {str(e)}")
            return False, {"error": f"创建支付请求失败: {str(e)}"}
    
    @staticmethod
    def process_payment_callback(
        db: Session, 
        order_no: str, 
        payment_id: str, 
        status: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理支付回调"""
        try:
            # 查询订单
            order = db.query(Order).filter(
                Order.order_no == order_no,
                Order.status == OrderStatus.PENDING
            ).first()
            
            if not order:
                return False, {"True": "订单不存在或状态不正确,可能已被周期轮询或者前端检查处理"}
            
            # 支付成功
            if status == "SUCCESS":
                # 更新订单状态
                order.status = OrderStatus.PAID
                order.payment_id = payment_id
                order.payment_time = datetime.now()
                
                # 给用户增加积分
                success, result = CreditService.update_credits(
                    db=db,
                    user_id=order.user_id,
                    amount=order.credits,
                    type="purchase",
                    description=f"购买{order.credits}积分",
                    related_id=order.id
                )
                
                if not success:
                    logger.error(f"增加用户积分失败: {result.get('error')}")
                    return True, {"error": f"支付成功但增加积分失败: {result.get('error')}"}
                
                # 更新订单为已完成状态
                order.status = OrderStatus.COMPLETED
                
                db.commit()
                return True, {"message": "支付成功并已增加积分"}
            else:
                # 支付失败，更新订单状态
                order.status = OrderStatus.CANCELLED
                db.commit()
                return False, {"error": "支付失败"}
        except Exception as e:
            db.rollback()
            logger.error(f"处理支付回调失败: {str(e)}")
            return False, {"error": f"处理支付回调失败: {str(e)}"}
        
    @staticmethod
    def get_user_orders(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Order]:
        """获取用户订单列表"""
        return db.query(Order).filter(
            Order.user_id == user_id,
            Order.is_deleted == False
        ).order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_order_detail(db: Session, order_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """获取订单详情"""
        # 联合查询订单及商品信息
        result = db.query(
            Order, 
            Product.name.label("product_name"),
            Product.description.label("product_description"),
            Product.image_url.label("product_image_url")
        ).join(
            Product, 
            Order.product_id == Product.id
        ).filter(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.is_deleted == False
        ).first()
        
        if not result:
            return None
        
        order, product_name, product_description, product_image_url = result
        
        # 构建响应数据
        order_dict = {
            "id": order.id,
            "order_no": order.order_no,
            "amount": order.amount,
            "credits": order.credits,
            "status": order.status,
            "payment_id": order.payment_id,
            "payment_time": order.payment_time,
            "refund_time": order.refund_time,
            "remark": order.remark,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "product_name": product_name,
            "product_description": product_description,
            "product_image_url": product_image_url
        }
        
        return order_dict 

    @staticmethod
    async def query_payment_status(db: Session, order_id: int) -> Tuple[bool, Dict[str, Any]]:
        """查询支付状态并更新订单"""
        # 获取或创建锁
        if order_id not in credit_processing_locks:
            credit_processing_locks[order_id] = threading.Lock()
        
        # 使用锁保护关键部分
        with credit_processing_locks[order_id]:
            try:
                # 查询订单
                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    return False, {"error": "订单不存在"}
                
                if order.status != OrderStatus.PENDING:
                    # 订单已处理，直接返回状态
                    return True, {
                        "order_id": order.id, 
                        "status": order.status,
                        "paid": order.status in [OrderStatus.PAID, OrderStatus.COMPLETED]
                    }
                
                # 调用Java支付网关查询订单状态
                payment_url = f"{settings.PAYMENT_GATEWAY_URL}/api/pay/query-status"
                
                payment_data = {
                    "outTradeNo": order.order_no
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(payment_url, json=payment_data)
                    result = response.json()
                
                if response.status_code != 200 or result.get("code") != 200:
                    return False, {"error": f"查询支付状态失败: {result.get('message', '未知错误')}"}
                
                payment_result = result.get("data", {})
                trade_state = payment_result.get("tradeState", "")
                
                # 处理支付结果
                if trade_state == "SUCCESS":
                    # 再次检查订单状态，确保在加锁期间没有被其他线程更新
                    order = db.query(Order).filter(Order.id == order_id).first()
                    if order.status != OrderStatus.PENDING:
                        return True, {
                            "order_id": order.id, 
                            "status": order.status,
                            "paid": order.status in [OrderStatus.PAID, OrderStatus.COMPLETED]
                        }
                    
                    # 更新订单为已支付
                    order.status = OrderStatus.PAID
                    order.payment_id = payment_result.get("transaction_id")
                    order.payment_time = datetime.now()
                    
                    # 给用户增加积分
                    success, credit_result = CreditService.update_credits(
                        db=db,
                        user_id=order.user_id,
                        amount=order.credits,
                        type="purchase",
                        description=f"购买{order.credits}积分",
                        related_id=order.id
                    )
                    
                    if success:
                        order.status = OrderStatus.COMPLETED
                        db.commit()
                        # 清理锁
                        if order_id in credit_processing_locks:
                            del credit_processing_locks[order_id]
                        return True, {
                            "order_id": order.id,
                            "status": order.status,
                            "paid": True,
                            "message": "支付成功"
                        }
                    else:
                        db.rollback()
                        return False, {"error": f"支付成功但增加积分失败: {credit_result.get('error')}"}
                
                elif trade_state in ["CLOSED", "REVOKED", "PAYERROR"]:
                    # 支付失败或取消
                    order.status = OrderStatus.CANCELLED
                    db.commit()
                    return True, {
                        "order_id": order.id,
                        "status": order.status,
                        "paid": False,
                        "message": "支付失败或已取消"
                    }
                
                else:
                    # 支付处理中或其他状态
                    return True, {
                        "order_id": order.id,
                        "status": order.status,
                        "paid": False,
                        "message": f"支付进行中，状态: {trade_state}"
                    }
                
            except Exception as e:
                db.rollback()
                logger.error(f"查询支付状态失败: {str(e)}")
                return False, {"error": f"查询支付状态失败: {str(e)}"}
            finally:
                # 在特定情况下清理锁
                if order_id in credit_processing_locks and order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REFUNDED]:
                    del credit_processing_locks[order_id]

    @staticmethod
    async def close_order(db: Session, order_no: str) -> Tuple[bool, Dict[str, Any]]:
        """关闭订单"""
        try:
            # 调用Java支付服务关闭订单
            close_url = f"{settings.PAYMENT_GATEWAY_URL}/api/pay/close-order/{order_no}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(close_url)
                result = response.json()
            
            if response.status_code == 200 and result.get("code") == 200:
                # 成功关闭订单
                # 更新本地订单状态
                order = db.query(Order).filter(Order.order_no == order_no).first()
                if order and order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.CANCELLED
                    db.commit()
                return True, {"message": "订单已关闭"}
            elif "该订单已支付" in result.get("message", ""):
                # 订单已支付，需要再次查询状态并处理积分
                logger.info(f"关闭订单失败，订单已支付: {order_no}")
                order = db.query(Order).filter(Order.order_no == order_no).first()
                if order and order.status == OrderStatus.PENDING:
                    # 再次查询订单状态
                    success, query_result = await OrderService.query_payment_status(db, order.id)
                    if success and query_result.get("paid", False):
                        return True, {"message": "订单已支付，已处理积分"}
                    else:
                        return False, {"error": "订单已支付但无法处理积分"}
                return True, {"message": "订单已处理"}
            else:
                # 其他错误
                return False, {"error": f"关闭订单失败: {result.get('message', '未知错误')}"}
        except Exception as e:
            logger.error(f"关闭订单请求失败: {str(e)}")
            return False, {"error": f"关闭订单请求失败: {str(e)}"} 