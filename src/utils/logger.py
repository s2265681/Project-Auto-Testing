"""
日志管理模块
Logging management module
"""
import sys
from loguru import logger
from .config import Config

# 配置日志
logger.remove()  # 移除默认处理器

# 添加控制台输出
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=Config.LOG_LEVEL,
    colorize=True
)

# 添加文件输出
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=Config.LOG_LEVEL
)

def get_logger(name: str = __name__):
    """
    获取logger实例
    Get logger instance
    
    Args:
        name: 模块名称 module name
        
    Returns:
        logger实例 logger instance
    """
    return logger.bind(name=name) 