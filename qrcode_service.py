import re
from pyzbar import pyzbar
import cv2
from models import QRCodeType, QR_TYPE_NAMES, QR_TYPE_PREFIXES

class QRCodeService:
    @staticmethod
    def decode_qrcode(image):
        """解码图像中的二维码"""
        return pyzbar.decode(image)
    
    @staticmethod
    def identify_qrcode_type(qr_data):
        """识别二维码类型"""
        if not qr_data:
            return QRCodeType.UNKNOWN, QR_TYPE_NAMES[QRCodeType.UNKNOWN]
        
        # 检查每种类型的前缀
        for qr_type, prefixes in QR_TYPE_PREFIXES.items():
            for prefix in prefixes:
                if qr_data.lower().startswith(prefix.lower()):
                    return qr_type, QR_TYPE_NAMES[qr_type]
        
        # 特殊情况处理
        # 微信支付特殊情况
        if re.search(r'(微信支付|wxpay)', qr_data, re.I):
            return QRCodeType.WX_PAY, QR_TYPE_NAMES[QRCodeType.WX_PAY]
        
        # 支付宝特殊情况
        if re.search(r'(支付宝|alipay)', qr_data, re.I):
            return QRCodeType.ALIPAY, QR_TYPE_NAMES[QRCodeType.ALIPAY]
        
        # 云闪付特殊情况
        if re.search(r'(银联|云闪付|unionpay)', qr_data, re.I):
            return QRCodeType.UNION_PAY, QR_TYPE_NAMES[QRCodeType.UNION_PAY]
        
        # 银行支付特殊情况
        if re.search(r'(icbc|ccb|abc|boc|cmb|bankcard|网银|手机银行|转账)', qr_data, re.I):
            return QRCodeType.BANK_PAY, QR_TYPE_NAMES[QRCodeType.BANK_PAY]
        
        # 微信特殊情况
        if re.search(r'(微信|weixin)', qr_data, re.I) and not re.search(r'(支付|pay)', qr_data, re.I):
            return QRCodeType.WEIXIN, QR_TYPE_NAMES[QRCodeType.WEIXIN]
        
        # 抖音特殊情况
        if re.search(r'(抖音|douyin|tiktok)', qr_data, re.I):
            return QRCodeType.DOUYIN, QR_TYPE_NAMES[QRCodeType.DOUYIN]
        
        # 淘宝特殊情况
        if re.search(r'(淘宝|taobao)', qr_data, re.I):
            return QRCodeType.TAOBAO, QR_TYPE_NAMES[QRCodeType.TAOBAO]
        
        # 京东特殊情况
        if re.search(r'(京东|jd\.com)', qr_data, re.I):
            return QRCodeType.JD, QR_TYPE_NAMES[QRCodeType.JD]
        
        # 美团特殊情况
        if re.search(r'(美团|meituan)', qr_data, re.I):
            return QRCodeType.MEITUAN, QR_TYPE_NAMES[QRCodeType.MEITUAN]
        
        # 滴滴特殊情况
        if re.search(r'(滴滴|didi)', qr_data, re.I):
            return QRCodeType.DIDI, QR_TYPE_NAMES[QRCodeType.DIDI]
        
        # URL类型
        if re.search(r'^https?://', qr_data, re.I):
            return QRCodeType.URL, QR_TYPE_NAMES[QRCodeType.URL]
        
        # 默认为文本类型
        return QRCodeType.TEXT, QR_TYPE_NAMES[QRCodeType.TEXT]
    
    @staticmethod
    def is_payment_qrcode(qr_data):
        """判断二维码是否为收款码"""
        # 微信支付正则
        wechat_pattern = r'^(wxp://|https?://payapp\.weixin\.qq\.com/|weixin://)'
        if re.search(wechat_pattern, qr_data, re.I):
            return True, "微信收款码"
        
        # 支付宝正则（扩展版）
        alipay_pattern = r'(https?://(qr|mapi)\.alipay\.com/|alipays://platformapi/startapp\?|ALIPAY:\/\/|支付宝|alipay)'
        if re.search(alipay_pattern, qr_data, re.I):
            return True, "支付宝收款码"
        
        # 银联云闪付正则
        if re.search(r'(unionpay|upapi|uppay|银联|云闪付)', qr_data, re.I):
            return True, "云闪付收款码"
        
        # 银行直连正则
        bank_pattern = r'(icbc|ccb|abc|boc|cmb|bankcard|网银|手机银行|转账)'
        if re.search(bank_pattern, qr_data, re.I):
            return True, "银行收款码"
        
        # 金额参数检测 - 提高优先级，放在平台检测前
        if re.search(r'(amount|money|total_fee)=[\d.]+', qr_data):
            return True, "含金额参数的收款码"
        
        # 支付平台正则 - 更严格的条件
        platform_pattern = r'(pay|付款|shoukuan|收钱|收款|platform|qrcode)'
        if re.search(platform_pattern, qr_data, re.I) and len(qr_data) < 150 and not re.search(r'http', qr_data, re.I):
            return True, "第三方支付平台"
        
        return False, ""