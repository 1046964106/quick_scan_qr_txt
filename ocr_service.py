import cv2
from PIL import Image
import io
import re
from paddleocr import PaddleOCR
from models import ImageType, IMAGE_TYPE_NAMES

# 初始化PaddleOCR - 禁用日志输出
ocr = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False, show_log=False)

class OCRService:
    @staticmethod
    def detect_idcard(image):
        """检测是否为身份证"""
        # 使用OCR识别文本
        try:
            # 转换为PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            img_bytes = io.BytesIO()
            pil_img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # 使用PaddleOCR识别
            result = ocr.ocr(img_bytes.getvalue(), cls=True)
            
            # 提取文本和位置信息
            texts = []
            text_boxes = []
            for line in result:
                for item in line:
                    text = item[1][0]  # 获取识别的文本
                    box = item[0]      # 获取文本框位置
                    texts.append(text.lower())
                    text_boxes.append((text.lower(), box))
            
            # 合并文本
            text = " ".join(texts)
            
            # 排除驾驶证
            driving_keywords = ["驾驶证", "驾驶员", "准驾车型", "档案编号", "机动车驾驶证"]
            if any(keyword in text for keyword in driving_keywords):
                return False
            
            # 身份证正面关键词（按照身份证上的顺序排列）
            front_keywords = ["姓名", "性别", "民族", "出生", "住址", "公民身份号码"]
            
            # 身份证反面关键词
            back_keywords = ["签发机关", "签发日期", "有效期限", "有效期"]
            
            # 检查是否为身份证正面
            front_match_count = sum(1 for keyword in front_keywords if keyword in text)
            is_front = front_match_count >= 3
            
            # 检查是否为身份证反面
            back_match_count = sum(1 for keyword in back_keywords if keyword in text)
            is_back = back_match_count >= 2
            
            # 检查关键词是否按顺序出现（仅对正面进行检查）
            if is_front:
                found_keywords = []
                for keyword in front_keywords:
                    if keyword in text:
                        found_keywords.append(keyword)
                
                # 检查关键词顺序
                if len(found_keywords) >= 3:  # 至少找到3个关键词
                    # 获取关键词在原始front_keywords中的索引
                    indices = [front_keywords.index(kw) for kw in found_keywords]
                    # 检查索引是否是递增的（保持顺序）
                    is_ordered = all(indices[i] < indices[i+1] for i in range(len(indices)-1))
                    
                    if is_ordered:
                        # 身份证号码格式
                        id_pattern = r'[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9xX]'
                        id_match = re.search(id_pattern, text.replace(" ", ""))
                        
                        # 如果关键词顺序正确，且找到身份证号码格式，则判定为身份证正面
                        if id_match:
                            return {"is_idcard": True, "side": "front"}
                        
                        # 如果关键词顺序正确，且包含"居民身份证"字样，也判定为身份证正面
                        if "居民身份证" in text:
                            return {"is_idcard": True, "side": "front"}
                        
                        # 如果找到4个以上关键词且顺序正确，也判定为身份证正面
                        if len(found_keywords) >= 4:
                            return {"is_idcard": True, "side": "front"}
            
            # 如果是身份证反面
            if is_back:
                # 检查是否包含"中华人民共和国"字样，增加判断准确性
                if "中华人民共和国" in text:
                    return {"is_idcard": True, "side": "back"}
                
                # 如果包含至少3个反面关键词，也判定为身份证反面
                if back_match_count >= 3:
                    return {"is_idcard": True, "side": "back"}
            
            # 如果上述条件都不满足，但明确包含"居民身份证"字样，也可能是身份证
            if "居民身份证" in text and "公民身份号码" in text:
                return {"is_idcard": True, "side": "front"}
                
            return False
            
        except Exception as e:
            from app import app
            app.logger.error(f"身份证检测出错: {str(e)}")
            return False

    @staticmethod
    def detect_driverCard(image):
        """检测是否为驾驶证"""
        try:
            # 转换为PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            img_bytes = io.BytesIO()
            pil_img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # 使用PaddleOCR识别
            result = ocr.ocr(img_bytes.getvalue(), cls=True)
            
            # 提取文本和位置信息
            texts = []
            text_positions = []
            for line in result:
                for item in line:
                    text = item[1][0]  # 获取识别的文本
                    box = item[0]      # 获取文本框位置
                    # 计算文本框中心点的y坐标
                    y_center = sum(point[1] for point in box) / 4
                    texts.append(text.lower())
                    text_positions.append((text.lower(), y_center))
            
            # 按照y坐标排序文本
            text_positions.sort(key=lambda x: x[1])
            ordered_texts = [item[0] for item in text_positions]
            
            # 合并文本
            text = " ".join(texts)
            ordered_text = " ".join(ordered_texts)
            
            # 排除身份证
            id_keywords = ["居民身份证", "公民身份号码"]
            if any(keyword in text for keyword in id_keywords) and "驾驶证" not in text and "驾驶员" not in text:
                return False
            
            # 驾驶证必须包含的关键词
            essential_keywords = ["驾驶证", "驾驶员", "机动车驾驶证"]
            if not any(keyword in text for keyword in essential_keywords):
                return False
            
            # 驾驶证正面关键词（按照驾驶证上的顺序排列）
            front_keywords = ["姓名", "性别", "国籍", "住址", "出生日期", "初次领证日期", "准驾车型"]
            
            # 驾驶证副页(反面)关键词
            back_keywords = ["档案编号", "记分", "发证机关", "有效期限"]
            
            # 检查正面关键词匹配数量和顺序
            front_match_count = sum(1 for keyword in front_keywords if keyword in text)
            
            # 检查反面关键词匹配数量
            back_match_count = sum(1 for keyword in back_keywords if keyword in text)
            
            # 检查关键词在有序文本中的顺序
            front_ordered = True
            last_index = -1
            for keyword in front_keywords:
                if keyword in ordered_text:
                    current_index = ordered_text.find(keyword)
                    if current_index < last_index:
                        front_ordered = False
                        break
                    last_index = current_index
            
            # 判断是正面还是反面
            if front_match_count >= 3 and front_ordered:
                return {"is_drivercard": True, "side": "front"}
            elif back_match_count >= 2:
                return {"is_drivercard": True, "side": "back"}
            elif "驾驶证" in text or "机动车驾驶证" in text:
                # 根据关键词数量判断
                if front_match_count > back_match_count:
                    return {"is_drivercard": True, "side": "front"}
                elif back_match_count > front_match_count:
                    return {"is_drivercard": True, "side": "back"}
                else:
                    return {"is_drivercard": True, "side": "unknown"}
                
            return False
            
        except Exception as e:
            from app import app
            app.logger.error(f"驾驶证检测出错: {str(e)}")
            return False

    @staticmethod
    def validate_card_number(card_number):
        """
        使用Luhn算法验证银行卡号
        """
        try:
            # 移除空格和连字符
            card_number = card_number.replace(' ', '').replace('-', '')
            
            # 检查是否全是数字
            if not card_number.isdigit():
                return False
                
            # 检查长度
            if not (15 <= len(card_number) <= 19):
                return False
                
            # Luhn算法
            sum = 0
            num_digits = len(card_number)
            oddeven = num_digits & 1
            
            for i in range(num_digits):
                digit = int(card_number[i])
                
                if ((i & 1) ^ oddeven) == 0:
                    digit = digit * 2
                if digit > 9:
                    digit = digit - 9
                    
                sum = sum + digit
                
            return (sum % 10) == 0
        except:
            return False
    
    @staticmethod
    def detect_bankcard(image):
        """检测是否为银行卡"""
        try:
            # 转换为PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            img_bytes = io.BytesIO()
            pil_img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # 使用PaddleOCR识别
            result = ocr.ocr(img_bytes.getvalue(), cls=True)
            
            # 提取文本
            texts = []
            for line in result:
                for item in line:
                    text = item[1][0]  # 获取识别的文本
                    texts.append(text)
            
            # 合并文本
            text = " ".join(texts)
            
            # 银行卡号格式检测 (更严格的格式，16-19位数字，通常4位一组)
            bankcard_pattern = r'(\d{4}[ -]?){3,4}\d{1,4}'
            
            # 银行名称关键词
            bank_keywords = ["银行", "信用卡", "储蓄卡", "借记卡", "信用卡中心", "bank", "card"]
            
            # 检查银行卡号格式
            card_matches = re.findall(bankcard_pattern, text)
            
            # 如果没有找到符合格式的卡号，直接返回False
            if not card_matches:
                return False
            
            # 提取所有可能的卡号并验证
            valid_card = False
            for match in re.finditer(bankcard_pattern, text):
                # 提取数字
                card_num = ''.join(re.findall(r'\d', match.group(0)))
                
                # 验证长度 (银行卡通常为16-19位)
                if 15 <= len(card_num) <= 19:
                    # 使用Luhn算法验证卡号
                    if OCRService.validate_card_number(card_num):
                        valid_card = True
                        break
            
            # 检查银行关键词
            keyword_match = any(keyword in text.lower() for keyword in bank_keywords)
            
            # 图像比例检查 (银行卡通常是长方形，比例约为1.58:1)
            h, w = image.shape[:2]
            aspect_ratio = w / h if h > 0 else 0
            is_card_ratio = 1.4 < aspect_ratio < 1.8
            
            # 更严格的条件：必须同时满足卡号格式、关键词和图像比例
            # 或者满足有效的卡号验证和图像比例
            return (valid_card and is_card_ratio) or (card_matches and keyword_match and is_card_ratio)
        
        except Exception as e:
            from app import app
            app.logger.error(f"银行卡检测出错: {str(e)}")
            return False
    

    @staticmethod
    def perform_ocr(image_path):
        """执行OCR识别 获取数据"""
        try:
            # 使用PaddleOCR进行识别
            result = ocr.ocr(image_path, cls=True)
            
            # 提取识别文本
            texts = []
            for line in result:
                for item in line:
                    text = item[1][0]  # 获取识别的文本
                    confidence = item[1][1]  # 获取置信度
                    if confidence > 0.5:  # 只保留置信度高的结果
                        texts.append(text)
            
            # 合并文本
            return "\n".join(texts)
        except Exception as e:
            from app import app
            app.logger.error(f"OCR识别出错: {str(e)}")
            return ""

    @staticmethod
    def detect_vehicleCard(image):
        """检测是否为行驶证"""
        try:
            # 转换为PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            img_bytes = io.BytesIO()
            pil_img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            # 使用PaddleOCR识别
            result = ocr.ocr(img_bytes.getvalue(), cls=True)
            
            # 提取文本
            texts = []
            for line in result:
                for item in line:
                    text = item[1][0]  # 获取识别的文本
                    texts.append(text.lower())
            
            # 合并文本
            text = " ".join(texts)
            
            # 行驶证关键词
            vehicle_keywords = ["中华人民共和国机动车行驶证","行驶证", "机动车登记证书", "车辆识别代号", "核定载人","发动机号码", "档案编号","注册日期","核定载质量","备注"]
            
            # 行驶证正页特有关键词
            front_keywords = ["品牌型号", "车辆类型", "行驶证","所有人", "住址", "使用性质", "发证日期"]
            
            # 行驶证副页特有关键词
            back_keywords = ["检验记录",  "核定载人", "核定载质量","档案编号", "总质量","备注","整备质量","备注"]
            
            # 检查是否包含行驶证关键词
            if any(keyword in text for keyword in vehicle_keywords):
                # 判断正反面
                front_count = sum(1 for keyword in front_keywords if keyword in text)
                back_count = sum(1 for keyword in back_keywords if keyword in text)
                
                # 增加更严格的判断条件
                if front_count >= 3 and front_count > back_count:
                    return {"is_vehiclecard": True, "side": "front"}
                elif back_count >= 2 and back_count > front_count:
                    return {"is_vehiclecard": True, "side": "back"}
                elif "行驶证" in text:
                    # 如果明确包含"行驶证"字样，但无法确定正反面
                    return {"is_vehiclecard": True, "side": "unknown"}
            
            return False
            
        except Exception as e:
            from app import app
            app.logger.error(f"行驶证检测出错: {str(e)}")
            return False