from typing import List, Optional, Dict, Any, Tuple
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.user import User
from app.models.credit_record import CreditRecord, CreditRecordType
from app.schemas.credit import CreditRecordCreate

logger = logging.getLogger(__name__)


class CreditService:
    @staticmethod
    def update_credits(
        db: Session, 
        user_id: int, 
        amount: int, 
        type: str,
        description: Optional[str] = None,
        related_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        更新用户积分
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            amount: 积分变动量，正为增加，负为减少
            type: 变动类型
            description: 变动描述
            related_id: 相关ID，如作品ID
            
        Returns:
            成功状态和结果信息
        """
        try:
            # 查找用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, {"error": "用户不存在"}
            
            # 检查积分余额（如果是扣除积分）
            if amount < 0 and user.credits + amount < 0:
                return False, {"error": "积分余额不足"}
            
            # 更新用户积分
            user.credits += amount
            
            # 创建积分记录
            record = CreditRecord(
                user_id=user_id,
                amount=amount,
                balance=user.credits,
                type=type,
                description=description,
                related_id=related_id,
            )
            db.add(record)
            
            # 提交事务
            db.commit()
            db.refresh(record)
            
            return True, {"credit_record": record, "balance": user.credits}
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新积分时发生错误: {str(e)}")
            return False, {"error": f"更新积分失败: {str(e)}"}
    
    @staticmethod
    def get_user_credit_records(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[CreditRecord]:
        """
        获取用户的积分记录
        """
        return db.query(CreditRecord)\
            .filter(CreditRecord.user_id == user_id)\
            .order_by(desc(CreditRecord.created_at))\
            .offset(skip).limit(limit).all()
    
    @staticmethod
    def get_user_credit_balance(db: Session, user_id: int) -> Optional[int]:
        """
        获取用户的积分余额
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return user.credits
    
    @staticmethod
    def count_user_credit_records(db: Session, user_id: int) -> int:
        """
        计算用户的积分记录总数
        """
        return db.query(func.count(CreditRecord.id))\
            .filter(CreditRecord.user_id == user_id)\
            .scalar()
    
    @staticmethod
    def ad_reward(
        db: Session, 
        user_id: int, 
        ad_type: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        广告奖励
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            ad_type: 广告类型，如"rewarded_video"
            
        Returns:
            成功状态和结果信息
        """
        try:
            from app.core.config import settings
            
            # 确定奖励积分数量
            reward_amount = settings.AD_REWARD_CREDITS
            
            # 查找用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, {"error": "用户不存在"}
            
            # 更新用户积分
            user.credits += reward_amount
            
            # 创建积分记录
            record = CreditRecord(
                user_id=user_id,
                amount=reward_amount,
                balance=user.credits,
                type="ad_reward",
                description=f"观看广告[{ad_type}]奖励积分",
            )
            db.add(record)
            
            # 提交事务
            db.commit()
            db.refresh(record)
            
            return True, {
                "reward_amount": reward_amount,
                "balance": user.credits,
                "credit_record": record
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"处理广告奖励时发生错误: {str(e)}")
            return False, {"error": f"处理广告奖励失败: {str(e)}"} 