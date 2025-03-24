import os
import json
import hashlib
import datetime
import urllib.parse
import requests
import base64
import shutil
import time
import threading
from collections import OrderedDict
from config import CACHE_DIR

# 内存缓存配置
MAX_MEMORY_CACHE_SIZE = 2000  # 最大内存缓存项数
MEMORY_CACHE_TTL = 3600  # 内存缓存项的生存时间（秒）

# 缓存结果字典 - 内存缓存（使用OrderedDict实现简单的LRU）
class LRUCache(OrderedDict):
    def __init__(self, maxsize=MAX_MEMORY_CACHE_SIZE, ttl=MEMORY_CACHE_TTL):
        self.maxsize = maxsize
        self.ttl = ttl
        super().__init__()
    
    def __getitem__(self, key):
        # 检查是否过期
        value, timestamp = super().__getitem__(key)
        if time.time() - timestamp > self.ttl:
            del self[key]
            raise KeyError(key)
        
        # 移动到末尾（最近使用）
        self.move_to_end(key)
        return value
    
    def __setitem__(self, key, value):
        # 如果达到最大容量，删除最早使用的项
        if len(self) >= self.maxsize:
            oldest = next(iter(self))
            del self[oldest]
        
        # 存储值和时间戳
        super().__setitem__(key, (value, time.time()))
        self.move_to_end(key)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

# 初始化LRU缓存
RESULT_CACHE = LRUCache()

# 上次清理时间
LAST_CLEANUP_TIME = 0
# 清理间隔（秒）
CLEANUP_INTERVAL = 3600  # 默认1小时清理一次
# 最大缓存文件数量
MAX_CACHE_FILES = 1000

class CacheManager:
    def __init__(self, app):
        self.app = app
        self.cleanup_lock = threading.Lock()
    
    def get_file_hash(self, file_path=None, url=None, base64_data=None):
        """计算文件或数据的哈希值作为缓存键"""
        hasher = hashlib.md5()
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                buf = f.read(65536)  # 读取64k块
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        
        elif url:
            # 从URL中提取文件名
            try:
                # 解析URL
                parsed_url = urllib.parse.urlparse(url)
                # 获取路径部分
                path = parsed_url.path
                # 提取文件名
                filename = os.path.basename(path)
                # 如果文件名为空或没有扩展名，使用默认名称
                if not filename or '.' not in filename:
                    filename = "image.jpg"
                
                # 生成哈希值
                hasher.update(url.encode('utf-8'))
                hash_value = hasher.hexdigest()
                
                # 组合文件名和哈希值作为缓存键
                # 提取文件名（不含扩展名）和扩展名
                name, ext = os.path.splitext(filename)
                # 限制文件名长度，避免路径过长
                if len(name) > 20:
                    name = name[:20]
                # 组合新的缓存键
                return f"{name}_{hash_value[:10]}"
            except:
                # 如果提取失败，回退到原来的方式
                hasher.update(url.encode('utf-8'))
                return f"url_{hasher.hexdigest()}"
        
        elif base64_data:
            # 对于base64数据，只取前10000个字符计算哈希，避免过长
            hasher.update(base64_data[:10000].encode('utf-8') if isinstance(base64_data, str) else base64_data[:10000])
            return f"b64_{hasher.hexdigest()}"
        
        return None
    
    def clean_old_cache(self, days=7, max_files=MAX_CACHE_FILES):
        """
        清理缓存文件，基于时间和数量两个维度
        
        参数:
            days: 清理超过指定天数的文件
            max_files: 保留的最大文件数量
        """
        now = datetime.datetime.now()
        count_time = 0
        count_number = 0
        
        try:
            # 获取所有缓存文件及其修改时间
            cache_files = []
            for filename in os.listdir(CACHE_DIR):
                file_path = os.path.join(CACHE_DIR, filename)
                # 检查是否是文件
                if os.path.isfile(file_path):
                    # 获取文件修改时间
                    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    cache_files.append((file_path, file_time))
            
            # 基于时间维度清理
            for file_path, file_time in cache_files:
                # 如果文件超过指定天数，删除
                if (now - file_time).days > days:
                    os.remove(file_path)
                    count_time += 1
            
            # 如果剩余文件数量仍然超过最大限制，基于时间排序删除最旧的文件
            remaining_files = [(f, t) for f, t in cache_files if os.path.exists(f)]
            if len(remaining_files) > max_files:
                # 按修改时间排序
                remaining_files.sort(key=lambda x: x[1])
                # 删除最旧的文件，直到数量符合要求
                for file_path, _ in remaining_files[:len(remaining_files) - max_files]:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        count_number += 1
            
            self.app.logger.info(f"清理了 {count_time} 个过期缓存文件，{count_number} 个超量缓存文件")
        except Exception as e:
            self.app.logger.error(f"清理缓存文件时出错: {str(e)}")
    
    def check_and_clean_cache(self, days=7, max_files=MAX_CACHE_FILES):
        """检查是否需要清理缓存，并在需要时执行清理"""
        global LAST_CLEANUP_TIME
        
        # 使用锁防止多线程同时清理
        if not self.cleanup_lock.acquire(False):
            return
            
        try:
            current_time = time.time()
            # 如果距离上次清理时间超过了清理间隔，执行清理
            if current_time - LAST_CLEANUP_TIME > CLEANUP_INTERVAL:
                self.app.logger.info("开始定期清理缓存...")
                self.clean_old_cache(days, max_files)
                LAST_CLEANUP_TIME = current_time
        finally:
            self.cleanup_lock.release()
    
    def get_cached_result(self, cache_key):
        """获取缓存的识别结果，同时检查是否需要清理缓存"""
        # 检查是否需要清理缓存
        self.check_and_clean_cache()
        
        # 先检查内存缓存
        result = RESULT_CACHE.get(cache_key)
        if result is not None:
            return result
        
        # 再检查文件缓存
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    # 更新内存缓存
                    RESULT_CACHE[cache_key] = result
                    # 更新文件访问时间，以便LRU策略
                    os.utime(cache_file, None)
                    return result
            except Exception as e:
                self.app.logger.error(f"读取缓存文件出错: {str(e)}")
        
        return None
    
    def save_to_cache(self, cache_key, result):
        """保存识别结果到缓存"""
        # 检查是否需要清理缓存
        self.check_and_clean_cache()
        
        # 保存到内存缓存
        RESULT_CACHE[cache_key] = result
        
        # 保存到文件缓存
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
        except Exception as e:
            self.app.logger.error(f"保存缓存文件出错: {str(e)}")
    
    def clear_memory_cache(self):
        """清空内存缓存"""
        global RESULT_CACHE
        RESULT_CACHE.clear()
        self.app.logger.info("内存缓存已清空")
    
    def download_image(self, url):
        """下载网络图片到临时文件，支持缓存"""
        # 计算URL的哈希值
        cache_key = self.get_file_hash(url=url)
        # 从URL中提取文件扩展名
        try:
            parsed_url = urllib.parse.urlparse(url)
            path = parsed_url.path
            _, ext = os.path.splitext(path)
            # 如果没有扩展名或扩展名不是图片格式，使用默认扩展名
            if not ext or ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                ext = '.jpg'
        except:
            ext = '.jpg'
        
        # 使用缓存键和提取的扩展名组合缓存路径
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}{ext}")
        
        # 检查缓存
        if os.path.exists(cache_path):
            self.app.logger.info(f"使用缓存图片: {cache_path}")
            return cache_path, cache_key
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # 保存到缓存
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            return cache_path, cache_key
        except Exception as e:
            raise Exception(f"下载图片失败: {str(e)}")
    
    def save_base64_image(self, base64_data):
        """将Base64编码的图像保存到临时文件，支持缓存"""
        # 计算base64数据的哈希值
        cache_key = self.get_file_hash(base64_data=base64_data)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.jpg")
        
        # 检查缓存
        if os.path.exists(cache_path):
            self.app.logger.info(f"使用缓存图片: {cache_path}")
            return cache_path, cache_key
        
        try:
            # 移除可能的前缀
            if ',' in base64_data:
                base64_data = base64_data.split(',', 1)[1]
            
            # 解码Base64数据
            image_data = base64.b64decode(base64_data)
            
            # 保存到缓存
            with open(cache_path, 'wb') as f:
                f.write(image_data)
            
            return cache_path, cache_key
        except Exception as e:
            raise Exception(f"Base64图像处理失败: {str(e)}")