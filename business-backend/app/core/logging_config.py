import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 默认日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging(
    level="info", 
    log_file=None, 
    log_format=None, 
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5,
    console_output=True
):
    """
    设置应用日志
    
    参数:
        level (str): 日志级别 (debug, info, warning, error, critical)
        log_file (str, optional): 日志文件路径，不设置则不记录到文件
        log_format (str, optional): 日志格式
        max_bytes (int): 单个日志文件最大大小
        backup_count (int): 保留的备份日志文件数量
        console_output (bool): 是否同时输出到控制台
    """
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
    log_format = log_format or DEFAULT_LOG_FORMAT
    
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除已有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(log_format)
    
    # 控制台输出
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 文件输出
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 使用RotatingFileHandler进行日志轮转
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # 返回根日志器
    return root_logger 