import os
import logging
from logging.handlers import RotatingFileHandler
import codecs
import sys

# 环境变量设置
os.environ['OMP_THREAD_LIMIT'] = '100000'


# 缓存目录设置
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 日志配置
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'qr_orc_scan.log')
LOG_LEVEL = logging.DEBUG

# 自定义UTF-8编码的日志处理器
class UTF8RotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding='utf-8', delay=False):
        RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount, encoding, delay)
    
    def _open(self):
        return codecs.open(self.baseFilename, self.mode, self.encoding)

def setup_logger(app):
    """配置Flask应用的日志"""
    # 创建日志处理器 - 使用UTF-8编码
    handler = UTF8RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    
    # 设置日志格式
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)8s] %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 清除现有的处理器，避免重复
    app.logger.handlers = []
    
    # 添加处理器到应用日志
    app.logger.addHandler(handler)
    app.logger.addHandler(console_handler)
    
    # 设置日志级别
    app.logger.setLevel(logging.INFO)
    
    # 禁用Werkzeug默认日志
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.disabled = True
    
    # 配置根日志器，但不添加重复的处理器
    root_logger = logging.getLogger()
    root_logger.handlers = []  # 清除根日志器的处理器
    app.logger.info("图像识别服务初始化完成")
    app.logger.info(f'缓存目录: {CACHE_DIR}')