from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# 创建SQLAlchemy引擎
engine = create_engine(
    settings.DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600,  # 连接池回收时间
    echo=False,  # 生产环境设为False
)

# 创建SessionLocal类，每个实例都是一个数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类，SQLAlchemy模型将继承这个类
Base = declarative_base()


# 依赖项函数，用于在路由中获取数据库会话
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 