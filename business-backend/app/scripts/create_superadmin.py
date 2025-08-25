#!/usr/bin/env python3
"""
创建超级管理员账号脚本

运行方式：
python -m app.scripts.create_superadmin
"""

import sys
import os
from pathlib import Path
import argparse

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.admin import AdminService
from app.schemas.admin import AdminCreate


def create_superadmin(username: str, password: str) -> None:
    """创建超级管理员账号"""
    db = SessionLocal()
    try:
        # 检查用户名是否已存在
        existing_admin = AdminService.get_admin_by_username(db, username)
        if existing_admin:
            print(f"用户名 '{username}' 已存在，无法创建")
            return
        
        # 创建管理员
        admin_create = AdminCreate(username=username, password=password)
        admin = AdminService.create_admin(db, admin_create)
        
        print(f"成功创建超级管理员: {admin.username} (ID: {admin.id})")
    
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建超级管理员账号")
    parser.add_argument("--username", default="admin", help="管理员用户名")
    parser.add_argument("--password", default="admin123", help="管理员密码")
    
    args = parser.parse_args()
    
    print("开始创建超级管理员账号...")
    create_superadmin(args.username, args.password)
    print("操作完成!") 