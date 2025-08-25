#!/usr/bin/env python3
"""
数据库初始化脚本

运行方式：
python -m scripts.init_db
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.system_config import SystemConfig
from app.services.system_config import SystemConfigService
from scripts.create_initial_styles import create_initial_styles


def init_db(db: Session) -> None:
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")
    
    # 初始化系统配置
    SystemConfigService.initialize_default_configs(db)
    print("系统配置初始化完成")
    
    # 创建初始风格数据
    create_initial_styles(db)
    print("风格数据初始化完成")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("开始初始化数据库...")
        init_db(db)
        print("数据库初始化完成!")
    finally:
        db.close() 