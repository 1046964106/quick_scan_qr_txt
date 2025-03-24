import cv2
import os
import time
from PIL import Image
import io
import numpy as np
from models import ImageType, IMAGE_TYPE_NAMES
from ocr_service import OCRService
from qrcode_service import QRCodeService
"""
图片处理器,分别处理图片,相关操作
"""
class ImageProcessor:
    def __init__(self, app):
        self.app = app
    
    def identify_image_type(self, image_path):
        """识别图片类型"""
        try:
            # 读取图像
            image_cv = cv2.imread(image_path)
            if image_cv is None:
                return ImageType.UNKNOWN, IMAGE_TYPE_NAMES[ImageType.UNKNOWN], None
            
            # 检测是否为二维码
            qr_results = QRCodeService.decode_qrcode(image_cv)
            if qr_results:
                return ImageType.QRCODE, IMAGE_TYPE_NAMES[ImageType.QRCODE], None
            
            # 检测是否为身份证
            idcard_result = OCRService.detect_idcard(image_cv)
            if idcard_result and isinstance(idcard_result, dict) and idcard_result.get("is_idcard"):
                return ImageType.IDCARD, IMAGE_TYPE_NAMES[ImageType.IDCARD], idcard_result.get("side", "unknown")
            
            # update 2023-08-23 14:55:20 新增驾驶证识别
            # 检测是否为驾驶证
            driverCard_result = OCRService.detect_driverCard(image_cv)
            if driverCard_result and isinstance(driverCard_result, dict) and driverCard_result.get("is_drivercard"):
                return ImageType.DRIVERCARD, IMAGE_TYPE_NAMES[ImageType.DRIVERCARD], driverCard_result.get("side", "unknown")
            # update 2023-08-23 14:55:20 新增行驶证识别
            # 检测是否为行驶证
            vehicleCard_result = OCRService.detect_vehicleCard(image_cv)
            if vehicleCard_result and isinstance(vehicleCard_result, dict) and vehicleCard_result.get("is_vehiclecard"):
                return ImageType.VEHICLECARD, IMAGE_TYPE_NAMES[ImageType.VEHICLECARD], vehicleCard_result.get("side", "unknown")

            # 检测是否为银行卡
            is_bankcard = OCRService.detect_bankcard(image_cv)
            if is_bankcard:
                return ImageType.BANKCARD, IMAGE_TYPE_NAMES[ImageType.BANKCARD], None
            
            # 默认为普通图片
            return ImageType.NORMAL, IMAGE_TYPE_NAMES[ImageType.NORMAL], None
        except Exception as e:
            self.app.logger.error(f"识别图片类型出错: {str(e)}")
            return ImageType.UNKNOWN, IMAGE_TYPE_NAMES[ImageType.UNKNOWN], None
    
    def mixed_recognition(self, image_path, use_color_filter=False, target_color=(30, 30, 30), is_temp=False):
        """
        混合识别函数：优先识别二维码，无二维码时进行文字识别
        
        参数:
            image_path: 图像路径
            use_color_filter: 是否使用颜色过滤 (默认False)
            target_color: 目标文字颜色 BGR格式 (默认黑色)
            is_temp: 是否为临时文件，处理完成后删除
        """
        try:
            # 读取图像
            image_cv = cv2.imread(image_path)
            if image_cv is None:
                return {"type": "error", "data": "无法读取图像"}
            
            # 图像尺寸优化
            h, w = image_cv.shape[:2]
            if max(h, w) > 1024:
                scale = 1024 / max(h, w)
                image_cv = cv2.resize(image_cv, (int(w*scale), int(h*scale)))
            
            # 识别图片类型
            image_type, image_type_name, side = self.identify_image_type(image_path)
            
            # 初始化返回结果字段
            result = {
                "imageType": image_type,
                "imageTypeName": image_type_name,  # 图片类型名称
                "ocrContent": "",  # 文字识别结果
                "qrContent": "",  # 二维码内容
                "qrType": "",  # 二维码类型
                "qrTypeName": "",  # 二维码类型名称
                "type": "text",  # 识别结果类型
                "qr_time": 0,  # 二维码识别时间
                "text_time": 0  # 文字识别时间
            }
            
            # 如果是身份证，添加正反面信息
            if image_type == ImageType.IDCARD and side:
                result["side"] = side
                result["sideName"] = "正面" if side == "front" else "反面"
            
            # 如果是驾驶证，添加正反面信息
            if image_type == ImageType.DRIVERCARD and side:
                result["side"] = side
                result["sideName"] = "正面" if side == "front" else "反面"
            
            # 如果是行驶证，添加正反面信息
            if image_type == ImageType.VEHICLECARD and side:
                result["side"] = side
                result["sideName"] = "正面" if side == "front" else "反面"

            # 二维码识别计时
            start_qr = time.time()
            qr_results = QRCodeService.decode_qrcode(image_cv)
            qr_time = time.time() - start_qr
            result["qr_time"] = round(qr_time, 2)
            
            # 如果有二维码结果
            if qr_results:
                qr_data = [qr.data.decode("utf-8", errors="ignore") for qr in qr_results]
                
                # 使用第一个二维码作为主要结果
                result["qrContent"] = qr_data[0] if qr_data else ""
                
                # 识别二维码类型
                if qr_data:
                    qr_type, qr_type_name = QRCodeService.identify_qrcode_type(qr_data[0])
                    result["qrType"] = qr_type
                    result["qrTypeName"] = qr_type_name
                
                # 设置结果类型为二维码
                result["type"] = "qr_code"
                
                # 保留原有的详细信息
                qr_types = []
                for data in qr_data:
                    qr_type, qr_type_name = QRCodeService.identify_qrcode_type(data)
                    is_payment, payment_type = QRCodeService.is_payment_qrcode(data)
                    qr_types.append({
                        "code": qr_type,
                        "name": qr_type_name,
                        "is_payment": is_payment,
                        "payment_type": payment_type if is_payment else None
                    })
            else:
                # 文字识别处理 - 使用PaddleOCR
                start_text = time.time()
                try:
                    # 使用OCR服务进行识别
                    text = OCRService.perform_ocr(image_path)
                    text_time = time.time() - start_text
                    result["text_time"] = round(text_time, 2)
                    
                    if text.strip():
                        result["type"] = "text"
                        result["ocrContent"] = text.strip()
                    else:
                        result["type"] = "none"
                except Exception as e:
                    self.app.logger.error(f"文字识别错误: {str(e)}")
                    result["type"] = "error"
                    result["error"] = f"文字识别错误: {str(e)}"
            
            return result
        finally:
            # 如果是临时文件，处理完成后删除
            if is_temp and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass