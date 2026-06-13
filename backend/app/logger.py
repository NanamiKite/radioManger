"""
日志配置模块
"""

import logging
import logging.handlers
from pathlib import Path
from app.config import settings

# 创建logs目录
log_dir = Path(settings.LOG_FILE).parent
log_dir.mkdir(exist_ok=True)

# 获取logger
logger = logging.getLogger("radiomanager")
logger.setLevel(getattr(logging, settings.LOG_LEVEL))

# 创建格式化器
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 文件处理器
file_handler = logging.handlers.RotatingFileHandler(
    settings.LOG_FILE,
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setFormatter(formatter)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
