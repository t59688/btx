from typing import List, Optional, Dict, Any
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.system_config import SystemConfig
from app.db.utils import get_base_query, soft_delete
from app.core.config import settings

logger = logging.getLogger(__name__)


class SystemConfigService:
    @staticmethod
    def get_config(db: Session, key: str) -> Optional[str]:
        """
        获取系统配置值
        """
        config = get_base_query(db, SystemConfig).filter(SystemConfig.config_key == key).first()
        return config.config_value if config else None
    
    @staticmethod
    def set_config(db: Session, key: str, value: str, description: Optional[str] = None) -> SystemConfig:
        """
        设置系统配置
        """
        config = get_base_query(db, SystemConfig).filter(SystemConfig.config_key == key).first()
        
        if not config:
            config = SystemConfig(
                config_key=key,
                config_value=value,
                description=description
            )
            db.add(config)
        else:
            config.config_value = value
            if description:
                config.description = description
        
        db.commit()
        db.refresh(config)
        
        # 更新内存中的配置
        # 使用settings类的类方法update
        from app.core.config import DynamicSettings
        DynamicSettings.update(key, value)
        
        # 输出更新后的配置
        print(f"\n===== 配置已更新: {key} =====")
        DynamicSettings.print_config(key)
        
        return config
    
    @staticmethod
    def delete_config(db: Session, key: str) -> bool:
        """
        软删除系统配置
        """
        config = get_base_query(db, SystemConfig).filter(SystemConfig.config_key == key).first()
        if not config:
            return False
        
        # 软删除记录
        success = soft_delete(db, config)
        
        # 如果删除成功，也从内存中删除
        if success:
            from app.core.config import DynamicSettings
            if key in DynamicSettings._config_store:
                del DynamicSettings._config_store[key]
                logger.debug(f"从内存中删除配置：{key}")
                
                # 输出删除信息
                print(f"\n===== 配置已删除: {key} =====")
                print(f"已从系统中移除配置项: {key}")
                print("============================\n")
                
                # 打印剩余配置
                print("当前系统所有配置:")
                DynamicSettings.print_config()
        
        return success
    
    @staticmethod
    def get_all_configs(db: Session, skip: int = 0, limit: int = 100) -> List[SystemConfig]:
        """
        获取所有系统配置
        """
        return get_base_query(db, SystemConfig).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_configs_by_prefix(db: Session, prefix: str) -> List[SystemConfig]:
        """
        获取指定前缀的所有系统配置
        """
        return get_base_query(db, SystemConfig).filter(SystemConfig.config_key.like(f"{prefix}%")).all()
    
    @staticmethod
    def get_config_map(db: Session, prefix: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        获取配置映射字典，包含值和描述
        """
        query = get_base_query(db, SystemConfig)
        
        if prefix:
            query = query.filter(SystemConfig.config_key.like(f"{prefix}%"))
            
        configs = query.all()
        
        return {config.config_key: {"value": config.config_value, "description": config.description} for config in configs}
    
    @staticmethod
    def initialize_default_configs(db: Session) -> None:
        """
        初始化默认系统配置
        """
        from app.core.config import Settings
        base_settings = Settings()
        
        # 默认配置列表
        default_configs = {
            "DEFAULT_CREDITS": str(base_settings.DEFAULT_CREDITS),
            "AD_REWARD_CREDITS": str(base_settings.AD_REWARD_CREDITS),
            "CREATE_COST_CREDITS": str(base_settings.CREATE_COST_CREDITS),
            "MAX_UPLOAD_SIZE": str(base_settings.MAX_UPLOAD_SIZE),
            "OPENAI_API_URL": base_settings.OPENAI_API_URL,
            "OPENAI_MODEL": base_settings.OPENAI_MODEL,
            "WECHAT_API_BASE_URL": base_settings.WECHAT_API_BASE_URL,
            "COS_REGION": base_settings.COS_REGION,
            "COS_BUCKET": base_settings.COS_BUCKET,
            "COS_DOMAIN": base_settings.COS_DOMAIN,
            "COS_UPLOAD_DIR": base_settings.COS_UPLOAD_DIR,
            "AD_PLATFORM": base_settings.AD_PLATFORM,
            "PAYMENT_CALLBACK_TOKEN": base_settings.PAYMENT_CALLBACK_TOKEN,
        }
        
        # 添加或更新配置
        for key, value in default_configs.items():
            config = get_base_query(db, SystemConfig).filter(SystemConfig.config_key == key).first()
            
            if not config:
                config = SystemConfig(
                    config_key=key,
                    config_value=value,
                    description=f"系统默认配置: {key}"
                )
                db.add(config)
            
        db.commit()
        
        # 重新加载内存中的配置
        from app.core.config import DynamicSettings
        DynamicSettings.initialize(db) 