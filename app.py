import os
import json
import tempfile
import shutil
import time
import signal
import functools
from flask import Flask, request, jsonify
from config import setup_logger, CACHE_DIR
from models import ImageType, IMAGE_TYPE_NAMES
from image_processor import ImageProcessor
from cache_manager import CacheManager

# 创建Flask应用
app = Flask(__name__)

# 设置日志
setup_logger(app)

# 初始化组件
cache_manager = CacheManager(app)

# 初始化上次清理时间
from cache_manager import LAST_CLEANUP_TIME, MAX_CACHE_FILES
LAST_CLEANUP_TIME = time.time()

# 启动时执行一次清理，确保服务启动时缓存是干净的
cache_manager.clean_old_cache(days=7, max_files=1000)
app.logger.info(f'缓存目录: {CACHE_DIR}')
image_processor = ImageProcessor(app)

# 超时处理装饰器
def timeout(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 定义超时处理函数
            def handle_timeout(signum, frame):
                raise TimeoutError(f"函数执行超时 ({seconds}秒)")

            # 仅在非Windows系统上使用信号
            if os.name != 'nt':
                # 设置信号处理
                original_handler = signal.signal(signal.SIGALRM, handle_timeout)
                # 设置闹钟
                signal.alarm(seconds)

            try:
                # 执行原始函数
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                # 记录执行时间
                if elapsed > seconds * 0.8:  # 如果执行时间超过阈值的80%，记录警告
                    app.logger.warning(f"函数 {func.__name__} 执行时间较长: {elapsed:.2f}秒")
                
                return result
            except TimeoutError as e:
                app.logger.error(f"超时错误: {str(e)}")
                # 返回超时错误响应
                return jsonify({
                    "code": 408,
                    "message": "请求处理超时",
                    "data": {
                        "type": "error",
                        "imageType": ImageType.UNKNOWN,
                        "imageTypeName": IMAGE_TYPE_NAMES[ImageType.UNKNOWN],
                        "error": "请求处理超时，请稍后重试"
                    }
                })
            finally:
                # 仅在非Windows系统上重置信号
                if os.name != 'nt':
                    # 取消闹钟
                    signal.alarm(0)
                    # 恢复原始信号处理器
                    signal.signal(signal.SIGALRM, original_handler)
        
        return wrapper
    return decorator

@app.before_request
def log_request():
    """记录请求信息"""
    if request.method == 'POST':
        # 记录基本请求信息
        app.logger.info(f'收到请求: {request.path} - 来自: {request.remote_addr}')
        
        # 记录请求参数（不记录图像数据本身）
        log_data = {}
        if request.form:
            for key in request.form:
                if key == 'image_base64':
                    log_data[key] = f'[BASE64数据，长度: {len(request.form[key])}]'
                else:
                    log_data[key] = request.form[key]
        
        if request.files:
            log_data['files'] = list(request.files.keys())
        
        if log_data:
            app.logger.info(f'请求参数: {json.dumps(log_data, ensure_ascii=False)}')

@app.after_request
def log_response(response):
    """记录响应信息"""
    try:
        # 尝试记录响应内容
        if response.is_json:
            response_data = response.get_json()
            # 对于大型响应，只记录类型和部分数据
            if response_data and isinstance(response_data, dict):
                log_data = {
                    "type": response_data.get("type", "unknown")
                }
                
                # 对于文本数据，记录前100个字符
                if "data" in response_data:
                    if isinstance(response_data["data"], str) and len(response_data["data"]) > 100:
                        log_data["data"] = response_data["data"][:100] + "..."
                    elif isinstance(response_data["data"], list):
                        log_data["data"] = f"[列表，包含{len(response_data['data'])}项]"
                    else:
                        log_data["data"] = response_data["data"]
                
                # 记录处理时间
                if "qr_time" in response_data:
                    log_data["qr_time"] = response_data["qr_time"]
                if "text_time" in response_data:
                    log_data["text_time"] = response_data["text_time"]
                
                app.logger.info(f'响应内容: {json.dumps(log_data, ensure_ascii=False)}')
    except Exception as e:
        app.logger.error(f'记录响应时出错: {str(e)}')
    
    return response

@app.route('/recognize', methods=['POST'])
@timeout(30)  # 设置30秒超时
def recognize_image_api():
    """
        图像识别API - 支持网络图片URL、Base64编码的图像、本地图像路径和上传的图像文件
        参数:
            image_url:      网络图片URL
            image_base64:   Base64编码的图像数据
            image_path:     本地图像路径（绝对路径）
            image:          上传的图像文件
    """
    temp_path = None
    cache_key = None
    
    try:
        # 获取请求中的图像数据
        if 'image_url' in request.form:
            # 处理网络图片URL
            image_url = request.form['image_url']
            app.logger.info(f'处理网络图片: {image_url}')
            
            # 检查URL缓存
            cache_key = cache_manager.get_file_hash(url=image_url)
            cached_result = cache_manager.get_cached_result(cache_key)
            if cached_result:
                app.logger.info(f'使用缓存结果: {cache_key}')
                # 确保返回格式一致
                return jsonify({
                    "code": 200,
                    "message": "成功",
                    "data": cached_result
                })
            
            # 下载图片
            temp_path, cache_key = cache_manager.download_image(image_url)
            result = image_processor.mixed_recognition(temp_path, is_temp=False)  # 不删除缓存图片
            
        elif 'image_base64' in request.form:
            # 处理Base64编码的图像
            base64_data = request.form['image_base64']
            
            # 检查base64缓存
            cache_key = cache_manager.get_file_hash(base64_data=base64_data)
            cached_result = cache_manager.get_cached_result(cache_key)
            if cached_result:
                app.logger.info(f'使用缓存结果: {cache_key}')
                # 确保返回格式一致
                return jsonify({
                    "code": 200,
                    "message": "成功",
                    "data": cached_result
                })
            
            # 保存图片
            temp_path, cache_key = cache_manager.save_base64_image(base64_data)
            result = image_processor.mixed_recognition(temp_path, is_temp=False)  # 不删除缓存图片
            
        elif 'image_path' in request.form:
            # 处理本地图像路径
            image_path = request.form['image_path']
            if os.path.exists(image_path):
                # 检查文件缓存
                cache_key = cache_manager.get_file_hash(file_path=image_path)
                cached_result = cache_manager.get_cached_result(cache_key)
                if cached_result:
                    app.logger.info(f'使用缓存结果: {cache_key}')
                    # 确保返回格式一致
                    return jsonify({
                        "code": 200,
                        "message": "成功",
                        "data": cached_result
                    })
                
                result = image_processor.mixed_recognition(image_path)
            else:
                # 统一错误返回格式
                return jsonify({
                    "code": 404,
                    "message": "文件不存在",
                    "data": {
                        "type": "error",
                        "imageType": ImageType.UNKNOWN,
                        "imageTypeName": IMAGE_TYPE_NAMES[ImageType.UNKNOWN],
                        "ocrContent": "",
                        "qrContent": "",
                        "qrType": "",
                        "qrTypeName": "",
                        "error": "文件不存在"
                    }
                })
                
        elif 'image' in request.files:
            # 处理上传的图像文件
            image_file = request.files['image']
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg').name
            image_file.save(temp_path)
            
            # 计算文件哈希
            cache_key = cache_manager.get_file_hash(file_path=temp_path)
            cached_result = cache_manager.get_cached_result(cache_key)
            if cached_result:
                app.logger.info(f'使用缓存结果: {cache_key}')
                os.remove(temp_path)  # 删除临时文件
                # 确保返回格式一致
                return jsonify({
                    "code": 200,
                    "message": "成功",
                    "data": cached_result
                })
            
            # 复制到缓存目录
            cache_path = os.path.join(CACHE_DIR, f"{cache_key}.jpg")
            shutil.copy2(temp_path, cache_path)
            os.remove(temp_path)  # 删除临时文件
            temp_path = cache_path
            
            result = image_processor.mixed_recognition(temp_path, is_temp=False)  # 不删除缓存图片
            
        else:
            # 统一错误返回格式
            return jsonify({
                "code": 400,
                "message": "未提供图像数据",
                "data": {
                    "type": "error",
                    "imageType": ImageType.UNKNOWN,
                    "imageTypeName": IMAGE_TYPE_NAMES[ImageType.UNKNOWN],
                    "ocrContent": "",
                    "qrContent": "",
                    "qrType": "",
                    "qrTypeName": "",
                    "error": "未提供图像数据"
                }
            })
        
        # 保存结果到缓存
        if cache_key:
            cache_manager.save_to_cache(cache_key, result)
        
        # 统一成功返回格式
        return jsonify({
            "code": 200,
            "message": "成功",
            "data": result
        })
        
    except Exception as e:
        # 统一错误返回格式
        error_result = {
            "code": 500,
            "message": str(e),
            "data": {
                "type": "error",
                "imageType": ImageType.UNKNOWN,
                "imageTypeName": IMAGE_TYPE_NAMES[ImageType.UNKNOWN],
                "ocrContent": "",
                "qrContent": "",
                "qrType": "",
                "qrTypeName": "",
                "error": str(e)
            }
        }
        return jsonify(error_result)
    finally:
        # 确保临时文件被删除
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"清理临时文件失败: {temp_path}, 错误: {str(e)}")