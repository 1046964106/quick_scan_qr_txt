import os
import sys
import json
import tempfile
from app import app
from image_processor import ImageProcessor
from cache_manager import CacheManager
from models import ImageType, IMAGE_TYPE_NAMES

# 初始化组件
cache_manager = CacheManager(app)
image_processor = ImageProcessor(app)

def process_from_cli():
    """处理命令行参数"""
    temp_path = None
    try:
        # 支持命令行参数
        if len(sys.argv) > 1:
            # 检查是否是启动服务器的命令
            if sys.argv[1] == 'server':
                port = 5000
                host = '0.0.0.0'  # 修改为0.0.0.0允许所有IP访问
                # 解析端口参数
                if len(sys.argv) > 2:
                    try:
                        port = int(sys.argv[2])
                    except:
                        pass
                        
                # 解析主机参数
                if len(sys.argv) > 3:
                    host = sys.argv[3]
                    
                print(f"启动图像识别服务，地址: {host}:{port}")
                app.logger.info(f"服务器监听地址: {host}:{port}")
                app.run(host=host, port=port, debug=False, threaded=True)
                return
                
            # 检查是否是URL
            elif sys.argv[1].startswith(('http://', 'https://')):
                try:
                    temp_path, cache_key = cache_manager.download_image(sys.argv[1])
                    result = image_processor.mixed_recognition(temp_path, is_temp=False)  # 不在mixed_recognition中删除
                    print(json.dumps(result, ensure_ascii=False))
                except Exception as e:
                    print(json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False))
                return
                    
            # 检查是否是Base64
            elif sys.argv[1].startswith(('data:image', 'base64:')):
                try:
                    base64_str = sys.argv[1]
                    if base64_str.startswith('base64:'):
                        base64_str = base64_str[7:]
                    temp_path, cache_key = cache_manager.save_base64_image(base64_str)
                    result = image_processor.mixed_recognition(temp_path, is_temp=False)  # 不在mixed_recognition中删除
                    print(json.dumps(result, ensure_ascii=False))
                except Exception as e:
                    print(json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False))
                return
            
            # 否则当作本地文件路径处理
            image_path = sys.argv[1]
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                print(json.dumps({"type": "error", "data": f"文件不存在 - {image_path}"}, ensure_ascii=False))
                return
            
            # 可选参数
            use_color_filter = False  # 是否启用颜色过滤
            
            result = image_processor.mixed_recognition(image_path, use_color_filter)
            print(json.dumps(result, ensure_ascii=False))
        else:
            # 无参数时显示帮助信息
            print("  识别本地图像: python main.py <图像路径>")
            print("  识别网络图像: python main.py <图像URL>")
            print("  识别Base64图像: python main.py base64:<Base64数据>")
            print("  启动HTTP服务: python main.py server [端口] [主机地址]")
    finally:
        # 确保临时文件被删除
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"已清理临时文件: {temp_path}")
            except Exception as e:
                print(f"清理临时文件失败: {temp_path}, 错误: {str(e)}")

# 使用示例
if __name__ == "__main__":
    process_from_cli()