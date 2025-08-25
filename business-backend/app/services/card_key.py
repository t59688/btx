from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from app.models.card_key import CardKey, CardKeyStatus
from app.models.user import User
from app.models.credit_record import CreditRecordType
from app.schemas.card_key import CardKeyCreate, CardKeyListParams, generate_card_key
from app.services.credit import CreditService

class CardKeyService:
    @staticmethod
    def get_by_id(db: Session, card_key_id: int) -> Optional[CardKey]:
        """根据ID获取卡密"""
        return db.query(CardKey).filter(CardKey.id == card_key_id).first()
    
    @staticmethod
    def get_by_key(db: Session, card_key: str) -> Optional[CardKey]:
        """根据卡密字符串获取卡密"""
        return db.query(CardKey).filter(CardKey.card_key == card_key).first()
    
    @staticmethod
    def create_batch(db: Session, obj_in: CardKeyCreate, admin_id: int) -> Dict[str, Any]:
        """批量创建卡密"""
        batch_no = f"BN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        
        # 创建指定数量的卡密
        card_keys = []
        for _ in range(obj_in.count):
            # 生成卡密，确保唯一
            while True:
                key = generate_card_key()
                if not CardKeyService.get_by_key(db, key):
                    break
            
            # 创建卡密对象
            card_key = CardKey(
                card_key=key,
                credits=obj_in.credits,
                batch_no=batch_no,
                created_by=admin_id,
                expired_at=obj_in.expired_at,
                status=CardKeyStatus.unused,
                remark=obj_in.remark,
            )
            db.add(card_key)
            card_keys.append(card_key)
        
        db.commit()
        
        # 构建返回结果
        return {
            "batch_no": batch_no,
            "count": obj_in.count,
            "credits": obj_in.credits,
            "expired_at": obj_in.expired_at,
        }
    
    @staticmethod
    def get_all(db: Session, params: CardKeyListParams) -> List[CardKey]:
        """获取卡密列表，支持过滤和排序"""
        query = db.query(CardKey)
        
        # 应用过滤条件
        if params.status:
            query = query.filter(CardKey.status == params.status)
        
        if params.batch_no:
            query = query.filter(CardKey.batch_no == params.batch_no)
        
        if params.created_start:
            query = query.filter(CardKey.created_at >= params.created_start)
        
        if params.created_end:
            query = query.filter(CardKey.created_at <= params.created_end)
        
        # 应用排序
        if params.order_desc:
            query = query.order_by(desc(getattr(CardKey, params.order_by)))
        else:
            query = query.order_by(asc(getattr(CardKey, params.order_by)))
        
        # 分页
        query = query.offset(params.skip).limit(params.limit)
        
        return query.all()
    
    @staticmethod
    def count(db: Session, status: Optional[str] = None, batch_no: Optional[str] = None) -> int:
        """统计卡密数量，支持过滤"""
        query = db.query(CardKey)
        
        if status:
            query = query.filter(CardKey.status == status)
        
        if batch_no:
            query = query.filter(CardKey.batch_no == batch_no)
        
        return query.count()
    
    @staticmethod
    def update_status(db: Session, card_key_id: int, status: str) -> Optional[CardKey]:
        """更新卡密状态"""
        card_key = CardKeyService.get_by_id(db, card_key_id)
        if not card_key:
            return None
        
        try:
            card_key_status = CardKeyStatus(status)
            card_key.status = card_key_status
            db.commit()
            db.refresh(card_key)
            return card_key
        except ValueError:
            return None
    
    @staticmethod
    def delete(db: Session, card_key_id: int) -> bool:
        """删除卡密"""
        card_key = CardKeyService.get_by_id(db, card_key_id)
        if not card_key:
            return False
        
        # 只允许删除未使用的卡密
        if card_key.status != CardKeyStatus.unused:
            return False
        
        db.delete(card_key)
        db.commit()
        return True
    
    @staticmethod
    def activate(db: Session, card_key_str: str, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        """用户激活卡密"""
        # 获取卡密
        card_key = CardKeyService.get_by_key(db, card_key_str)
        if not card_key:
            return False, {"error": "卡密不存在"}
        
        # 检查卡密状态
        if card_key.status != CardKeyStatus.unused:
            return False, {"error": "卡密已被使用或已失效"}
        
        # 检查卡密是否过期
        if card_key.expired_at and card_key.expired_at < datetime.now():
            card_key.status = CardKeyStatus.invalid
            db.commit()
            return False, {"error": "卡密已过期"}
        
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {"error": "用户不存在"}
        
        # 更新卡密状态
        card_key.status = CardKeyStatus.used
        card_key.used_at = datetime.now()
        card_key.used_by = user_id
        card_key.used_by_nickname = user.nickname
        
        # 为用户增加积分
        success, result = CreditService.update_credits(
            db=db,
            user_id=user_id,
            amount=card_key.credits,
            type=CreditRecordType.CARD_KEY,
            description=f"使用卡密 {card_key_str} 获得积分",
            related_id=card_key.id
        )
        
        if not success:
            db.rollback()
            return False, {"error": "增加积分失败"}
        
        db.commit()
        db.refresh(card_key)
        
        return True, {
            "credits": card_key.credits,
            "balance": result["balance"]
        } 