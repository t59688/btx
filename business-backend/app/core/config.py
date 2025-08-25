import os
import secrets
import logging
import sys
from typing import Any, Dict, List, Optional, Union, ClassVar
from pydantic_settings import BaseSettings
from pydantic import validator, AnyHttpUrl, field_validator
from pydantic_core.core_schema import ValidationInfo


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # 基础配置
    API_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    
    # 支付回调配置
    PAYMENT_CALLBACK_TOKEN: str = os.getenv("PAYMENT_CALLBACK_TOKEN", "xxxxxxxxxxx")
    
    # 数据库配置
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306") 
    DB_USER: str = os.getenv("DB_USER", "xxxxxxxxxxx")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "xxxxxxxxxxx")
    DB_NAME: str = os.getenv("DB_NAME", "ai_style_gallery")
    DATABASE_URI: Optional[str] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_uri(cls, v: Optional[str], info: ValidationInfo) -> str:
        if v:
            return v
        values = info.data
        return f"mysql+pymysql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"
    
    # 跨域配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # 微信小程序配置
    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "xxxxxxxxxxx")
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "xxxxxxxxxxx")
    WECHAT_API_BASE_URL: str = "https://api.weixin.qq.com"
    
    # 支付网关配置
    PAYMENT_GATEWAY_URL: str = os.getenv("PAYMENT_GATEWAY_URL", "xxxxxxxxxxx")
    
    # 腾讯云COS配置
    COS_SECRET_ID: str = os.getenv("COS_SECRET_ID", "xxxxxxxxxxx")
    COS_SECRET_KEY: str = os.getenv("COS_SECRET_KEY", "xxxxxxxxxxx")
    COS_REGION: str = os.getenv("COS_REGION", "ap-beijing")
    COS_BUCKET: str = os.getenv("COS_BUCKET", "xxxxxxxxxxx")
    COS_DOMAIN: str = os.getenv("COS_DOMAIN", "xxxxxxxxxxx")
    COS_UPLOAD_DIR: str = os.getenv("COS_UPLOAD_DIR", "xxxx")
    
    # OpenAI配置 (用于图像风格转换)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "xxxxxxxxxxx")
    OPENAI_API_URL: str = os.getenv("OPENAI_API_URL", "xxxxxxxxxxx")
    OPENAI_MODEL: str = os.getenv("OPENAI_API_URL", "xxxxxxxxxxx")
    OPENAI_IMAGE_MODEL: str = os.getenv("OPENAI_IMAGE_MODEL", "xxxxxxxxxxx")
    OPENAI_TIMEOUT: int = os.getenv("OPENAI_TIMEOUT", 600)
    
    # 积分配置
    DEFAULT_CREDITS: int = 20  # 新用户默认积分
    AD_REWARD_CREDITS: int = 10  # 广告奖励积分
    CREATE_COST_CREDITS: int = 10  # 创建作品消耗积分
    
    # 图片上传配置
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # 广告平台配置
    AD_PLATFORM: str = "微信广告"
    AD_APP_ID: str = os.getenv("AD_APP_ID", "")
    AD_APP_SECRET: str = os.getenv("AD_APP_SECRET", "")
    AD_UNIT_ID: str = os.getenv("AD_UNIT_ID", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'


class DynamicSettings:
    """
    动态设置类，从数据库加载配置
    """
    # 类变量，存储所有配置
    _config_store: ClassVar[Dict[str, str]] = {}
    _is_initialized: ClassVar[bool] = False
    
    # 基础设置实例，用于数据库连接等不能从数据库加载的配置
    _base_settings: Settings = Settings()
    
    def __getattr__(self, name: str) -> Any:
        """
        魔术方法，支持通过settings.CONFIG_NAME直接访问任意配置项
        如果CONFIG_NAME以大写字母开头，会在_config_store中查找对应键名
        """
        # 尝试获取内置属性
        try:
            return super().__getattr__(name)
        except AttributeError:
            pass
            
        # 如果属性名为大写，则视为配置项
        if name.isupper():
            # 先从数据库配置中获取
            value = self.get(name)
            if value is not None:
                return value
            
            # 再从环境变量获取
            env_value = os.getenv(name)
            if env_value is not None:
                return env_value
                
            # 最后返回空字符串
            return ""
        
        # 对于非大写属性名，保持正常的属性错误
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    @classmethod
    def initialize(cls, db_session=None):
        """
        从数据库初始化配置
        """
        if cls._is_initialized:
            return
        
        # 在第一次初始化时，如果没有提供db_session，则创建一个
        if db_session is None:
            # 避免循环导入
            from app.db.session import SessionLocal
            db_session = SessionLocal()
            close_session = True
        else:
            close_session = False
        
        try:
            # 导入服务
            from app.services.system_config import SystemConfigService
            
            # 获取所有配置
            configs = SystemConfigService.get_all_configs(db_session)
            
            if not configs:
                logger.warning("数据库中没有找到任何系统配置，将使用默认值")
            
            # 更新配置存储
            for config in configs:
                cls._config_store[config.config_key] = config.config_value
                
            # 标记为已初始化
            cls._is_initialized = True
            logger.info(f"从数据库加载了 {len(cls._config_store)} 个系统配置项")
            
        except Exception as e:
            logger.error(f"初始化系统配置时出错：{str(e)}")
            raise RuntimeError(f"无法从数据库加载系统配置：{str(e)}")
        finally:
            if close_session:
                db_session.close()
    
    @classmethod
    def update(cls, key: str, value: str):
        """
        更新内存中的配置
        """
        cls._config_store[key] = value
        logger.debug(f"更新配置：{key} = {value}")
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> str:
        """
        获取配置值
        """
        if not cls._is_initialized:
            logger.warning("尝试在初始化前访问配置，将返回默认值")
            return default
        return cls._config_store.get(key, default)
    
    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """
        获取整数配置值
        """
        value = cls.get(key, str(default))
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"配置{key}的值'{value}'不是有效的整数，使用默认值{default}")
            return default
    
    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """
        获取布尔配置值
        """
        value = cls.get(key, str(default)).lower()
        if value in ("1", "true", "yes", "y", "on"):
            return True
        elif value in ("0", "false", "no", "n", "off"):
            return False
        else:
            logger.warning(f"配置{key}的值'{value}'不是有效的布尔值，使用默认值{default}")
            return default
    
    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        """
        获取浮点数配置值
        """
        value = cls.get(key, str(default))
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"配置{key}的值'{value}'不是有效的浮点数，使用默认值{default}")
            return default
    
    @classmethod
    def get_all(cls) -> Dict[str, str]:
        """
        获取所有配置
        """
        return cls._config_store.copy()
    
    @classmethod
    def print_config(cls, key: str = None):
        """
        格式化打印配置信息，可选择打印单个配置或所有配置
        """
        if not cls._is_initialized:
            print("系统配置尚未初始化！")
            return
            
        if key:
            # 打印单个配置项
            if key in cls._config_store:
                value = cls._config_store[key]
                print(f"\n===== 配置详情: {key} =====")
                # 对敏感信息做脱敏处理
                if any(sensitive in key.lower() for sensitive in ["secret", "password", "key", "token"]):
                    if value and len(value) > 8:
                        masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:]
                    else:
                        masked_value = "********"
                    print(f"{key}: {masked_value}")
                else:
                    print(f"{key}: {value}")
                print("==========================\n")
            else:
                print(f"\n配置项 '{key}' 不存在！\n")
        else:
            # 打印所有配置
            all_configs = cls.get_all()
            print("\n========== 系统配置信息 ==========")
            if all_configs:
                for key, value in sorted(all_configs.items()):
                    # 对敏感信息做脱敏处理
                    if any(sensitive in key.lower() for sensitive in ["secret", "password", "key", "token"]):
                        if value and len(value) > 8:
                            masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:]
                        else:
                            masked_value = "********"
                        print(f"{key}: {masked_value}")
                    else:
                        print(f"{key}: {value}")
            else:
                print("未加载任何配置！")
            print("=================================\n")
    
    # 保留以下属性方法用于IDE智能提示和类型提示，但实际调用会通过__getattr__
    # 数据库相关配置 - 这些从Settings中获取，不受动态配置影响
    @property
    def API_STR(self) -> str:
        return self._base_settings.API_STR
    
    @property
    def SECRET_KEY(self) -> str:
        return self._base_settings.SECRET_KEY
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self._base_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def DATABASE_URI(self) -> str:
        return self._base_settings.DATABASE_URI


# 创建设置实例
settings = DynamicSettings()