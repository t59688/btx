#!/usr/bin/env python3
"""
初始化风格数据脚本

运行方式：
python -m scripts.create_initial_styles
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# 导入这一行，确保所有模型都被加载，避免循环引用问题
from app.db.base import Base

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.style import Style


# 初始风格数据
INITIAL_STYLES = [
    {
        "name": "油画肖像",
        "description": "经典油画风格的肖像效果，富有艺术质感和厚重感。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/oil_portrait.jpg",
        "category": "油画",
        "credits_cost": 10,
        "sort_order": 10,
    },
    {
        "name": "梵高星空",
        "description": "梵高《星空》风格，旋转的笔触和明亮的色彩。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/van_gogh.jpg",
        "category": "油画",
        "credits_cost": 10,
        "sort_order": 15,
    },
    {
        "name": "水彩画",
        "description": "轻盈透明的水彩画风格，色彩柔和自然。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/watercolor.jpg",
        "category": "水彩",
        "credits_cost": 10,
        "sort_order": 20,
    },
    {
        "name": "赛博朋克",
        "description": "霓虹灯光、高科技与复古未来主义相结合的赛博朋克风格。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/cyberpunk.jpg",
        "category": "数字艺术",
        "credits_cost": 15,
        "sort_order": 25,
    },
    {
        "name": "动漫风格",
        "description": "日式动漫风格，线条清晰，色彩明快。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/anime.jpg",
        "category": "动漫",
        "credits_cost": 8,
        "sort_order": 30,
    },
    {
        "name": "水墨国风",
        "description": "中国传统水墨画风格，意境深远。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/chinese_ink.jpg",
        "category": "国风",
        "credits_cost": 12,
        "sort_order": 35,
    },
    {
        "name": "波普艺术",
        "description": "色彩艳丽、对比强烈的波普艺术风格。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/pop_art.jpg",
        "category": "现代艺术",
        "credits_cost": 10,
        "sort_order": 40,
    },
    {
        "name": "素描铅笔",
        "description": "经典铅笔素描风格，呈现自然的明暗过渡。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/pencil_sketch.jpg",
        "category": "素描",
        "credits_cost": 8,
        "sort_order": 45,
    },
    {
        "name": "哥特风格",
        "description": "黑暗、神秘、庄严的哥特风格。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/gothic.jpg",
        "category": "暗黑",
        "credits_cost": 15,
        "sort_order": 50,
    },
    {
        "name": "未来主义",
        "description": "表现速度、动态和科技感的未来主义风格。",
        "preview_url": "https://your-cos.cos.accelerate.myqcloud.com/styles/futurism.jpg",
        "category": "现代艺术",
        "credits_cost": 12,
        "sort_order": 55,
    },
]


def create_initial_styles(db: Session):
    """创建初始风格数据"""
    existing_styles = db.query(Style).all()
    existing_style_names = [style.name for style in existing_styles]
    
    styles_to_add = []
    for style_data in INITIAL_STYLES:
        if style_data["name"] not in existing_style_names:
            style = Style(**style_data)
            styles_to_add.append(style)
    
    if styles_to_add:
        db.add_all(styles_to_add)
        db.commit()
        print(f"成功添加 {len(styles_to_add)} 个新风格")
    else:
        print("没有需要添加的新风格")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        create_initial_styles(db)
    finally:
        db.close() 