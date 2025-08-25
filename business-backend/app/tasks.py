import asyncio
import logging
from typing import Set, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.services.order import OrderService

logger = logging.getLogger(__name__)

# 存储正在检查的订单ID，避免重复处理
checking_orders: Set[int] = set()

# 跟踪订单检查次数
order_check_counts: Dict[int, int] = {}

async def check_payment_status_task():
    """周期性检查未完成的订单状态"""
    while True:
        try:
            db = SessionLocal()
            # 查询所有待支付的订单
            pending_orders = db.query(Order).filter(
                Order.status == OrderStatus.PENDING,
                Order.is_deleted == False,
                # 只检查30分钟内创建的订单
                Order.created_at > datetime.now() - timedelta(minutes=30000)
            ).all()
            
            for order in pending_orders:
                # 避免重复检查同一订单
                if order.id in checking_orders:
                    continue
                    
                checking_orders.add(order.id)
                try:
                    # 检查订单创建时间是否超过90秒
                    # 确保created_at是datetime类型
                    if isinstance(order.created_at, str):
                        try:
                            # 解析字符串格式的时间
                            created_at = datetime.strptime(order.created_at, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            logger.error(f"无法解析订单创建时间格式: {order.created_at}，订单号: {order.order_no}")
                            continue
                    else:
                        created_at = order.created_at
                    
                    # 计算时间差
                    now = datetime.now()
                    order_age = (now - created_at).total_seconds()
                    
                    # 记录日志，帮助调试
                    logger.info(f"订单 {order.order_no} 创建时间: {created_at}, 当前时间: {now}, 时间差: {order_age}秒")
                    
                    # 增加检查次数
                    order_check_counts[order.id] = order_check_counts.get(order.id, 0) + 1
                    check_count = order_check_counts[order.id]
                    
                    # 如果订单超过90秒且状态仍为未支付，直接关闭
                    if order_age > 90 and order.status == OrderStatus.PENDING:
                        logger.info(f"订单 {order.order_no} 已超过90秒未支付，尝试关闭订单")
                        success, result = await OrderService.close_order(db, order.order_no)
                        
                        if success:
                            logger.info(f"已关闭超时订单 {order.order_no}: {result.get('message')}")
                            # 清除检查计数
                            if order.id in order_check_counts:
                                del order_check_counts[order.id]
                        else:
                            logger.warning(f"关闭超时订单 {order.order_no} 失败: {result.get('error')}")
                    # 如果检查次数达到10次，关闭订单
                    elif check_count >= 10:
                        logger.info(f"订单 {order.order_no} 已检查 {check_count} 次，尝试关闭订单")
                        success, result = await OrderService.close_order(db, order.order_no)
                        
                        if success:
                            logger.info(f"已关闭订单 {order.order_no}: {result.get('message')}")
                            # 清除检查计数
                            if order.id in order_check_counts:
                                del order_check_counts[order.id]
                        else:
                            logger.warning(f"关闭订单 {order.order_no} 失败: {result.get('error')}")
                    else:
                        # 正常查询订单状态
                        success, result = await OrderService.query_payment_status(db, order.id)
                        if success:
                            logger.info(f"自动检查订单状态: ID={order.id}, 状态={result.get('status')}, 消息={result.get('message')}, 检查次数={check_count}")
                            
                            # 如果订单已完成或取消，清除检查计数
                            if result.get('status') in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REFUNDED]:
                                if order.id in order_check_counts:
                                    del order_check_counts[order.id]
                        else:
                            logger.warning(f"自动检查订单状态失败: ID={order.id}, 错误={result.get('error')}")
                finally:
                    # 无论成功失败，都从检查集合中移除
                    checking_orders.remove(order.id)
            
            db.close()
        except Exception as e:
            logger.error(f"订单状态检查任务异常: {str(e)}")
            if 'db' in locals():
                db.close()
        
        # 每10秒检查一次
        await asyncio.sleep(10)

async def check_all_orders_on_startup():
    """系统启动时检查所有可能存在问题的订单"""
    try:
        db = SessionLocal()
        # 查询过去24小时内创建的所有待支付订单
        pending_orders = db.query(Order).filter(
            Order.status == OrderStatus.PENDING,
            Order.is_deleted == False,
            Order.created_at > datetime.now() - timedelta(hours=24)
        ).all()
        
        logger.info(f"系统启动，正在检查 {len(pending_orders)} 个待支付订单")
        
        for order in pending_orders:
            try:
                # 查询支付状态
                success, result = await OrderService.query_payment_status(db, order.id)
                if success:
                    logger.info(f"系统启动检查订单: ID={order.id}, 状态={result.get('status')}, 消息={result.get('message')}")
                else:
                    logger.warning(f"系统启动检查订单失败: ID={order.id}, 错误={result.get('error')}")
            except Exception as e:
                logger.error(f"检查订单 {order.id} 时出错: {str(e)}")
        
        db.close()
    except Exception as e:
        logger.error(f"启动时检查订单状态异常: {str(e)}")
        if 'db' in locals():
            db.close()

# 存储任务引用
background_task = None

def start_background_tasks():
    """启动后台任务"""
    global background_task
    
    # 启动时检查所有订单
    asyncio.create_task(check_all_orders_on_startup())
    
    if background_task is None:
        logger.info("启动订单状态检查后台任务")
        background_task = asyncio.create_task(check_payment_status_task())

def stop_background_tasks():
    """停止后台任务"""
    global background_task
    
    if background_task:
        logger.info("停止订单状态检查后台任务")
        background_task.cancel()
        background_task = None

def add_order_to_check_queue(order_id: int):
    """添加订单到检查队列"""
    # 确保订单不在检查计数中，或重置计数
    order_check_counts[order_id] = 0
    logger.info(f"已将订单 ID={order_id} 添加到检查队列")
