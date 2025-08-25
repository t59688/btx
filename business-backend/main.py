import logging
import os
import sys

# 确保logs目录存在
if not os.path.exists("logs"):
    os.makedirs("logs")

# 导入自定义的日志配置
from app.core.logging_config import setup_logging

# 设置日志
log_file = os.getenv("LOG_FILE", "logs/app.log")  # 可通过环境变量配置日志文件路径
log_level = os.getenv("LOG_LEVEL", "info")  # 可通过环境变量配置日志级别
log_console = os.getenv("LOG_CONSOLE", "true").lower() == "true"  # 是否输出到控制台
setup_logging(level=log_level, log_file=None, console_output=log_console)

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
import json

from app.db.session import get_db, SessionLocal
from app.api.api import api_router
from app.core.config import settings, DynamicSettings
from app.tasks import start_background_tasks, stop_background_tasks

logger = logging.getLogger(__name__)
logger.info("应用启动中...")
logger.info(f"日志级别: {log_level.upper()}")
# logger.info(f"日志文件: {log_file if log_file else '未配置'}")

# 初始化系统配置
try:
    logger.info("正在从数据库加载系统配置...")
    db = SessionLocal()
    try:
        # 测试数据库连接
        db.execute(text("SELECT 1"))
        # 初始化系统配置
        DynamicSettings.initialize(db)
        
        # 输出配置信息到控制台
        DynamicSettings.print_config()
        
        logger.info("系统配置加载成功")
    except Exception as e:
        logger.error(f"从数据库加载系统配置失败: {str(e)}")
        print(f"错误: 无法从数据库加载系统配置: {str(e)}")
        sys.exit(1)
    finally:
        db.close()
except Exception as e:
    logger.error(f"连接数据库失败: {str(e)}")
    print(f"错误: 无法连接到数据库: {str(e)}")
    sys.exit(1)

app = FastAPI(
    title="AI风格转换画廊API",
    description="微信小程序AI风格转换画廊后端API",
    version="1.0.0",
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应设置为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,  # 增加预检请求缓存时间为24小时，减少OPTIONS请求频率
)

# 添加日志中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 记录请求信息
    path = request.url.path
    method = request.method
    query_params = str(request.query_params)
    client_host = request.client.host if request.client else "unknown"
    
    logger.info(f"请求开始 | {method} {path} | 客户端: {client_host} | 参数: {query_params}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    formatted_process_time = '{:.2f}'.format(process_time)
    
    # 记录响应信息
    logger.info(f"请求完成 | {method} {path} | 状态码: {response.status_code} | 处理时间: {formatted_process_time}s")
    
    return response

# 包含API路由
logger.info(f"注册API路由，路径前缀: {settings.API_STR}")
app.include_router(api_router, prefix=settings.API_STR)


@app.get("/")
def root():
    logger.debug("访问根路径")
    return {"message": "欢迎使用AI风格转换画廊API"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    logger.debug("执行健康检查")
    # 检查数据库连接
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
        logger.info("数据库连接正常")
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"数据库连接错误: {str(e)}")
    
    # 检查配置是否加载
    config_status = "ok" if DynamicSettings._is_initialized else "未初始化"
    
    return {
        "status": "running",
        "database": db_status,
        "config": config_status,
    }

@app.middleware("http")
async def auth_middleware(request, call_next):
    # 对OPTIONS请求直接放行，不执行认证逻辑
    if request.method == "OPTIONS":
        return await call_next(request)
        
    # 其他请求的认证逻辑
    # ...
    
    return await call_next(request)

@app.on_event("startup")
async def startup_event():
    # 其他启动代码...
    start_background_tasks()

@app.on_event("shutdown")
async def shutdown_event():
    # 其他关闭代码...
    stop_background_tasks()

if __name__ == "__main__":
    import uvicorn
    logger.info(f"以开发模式启动应用，监听地址: 0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 