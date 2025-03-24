# 图片类型枚举
class ImageType:
    """图片类型枚举"""
    QRCODE = "QRCODE"               # 二维码
    IDCARD = "IDCARD"               # 身份证
    BANKCARD = "BANKCARD"           # 银行卡
    NORMAL = "NORMAL"               # 普通图片
    DRIVERCARD = "DRIVERCARD"       # 驾驶证
    VEHICLECARD = "VEHICLECARD"     # 行驶证
    UNKNOWN = "UNKNOWN"             # 未知类型

# 图片类型名称映射
IMAGE_TYPE_NAMES = {
    ImageType.QRCODE: "二维码",
    ImageType.IDCARD: "身份证",
    ImageType.BANKCARD: "银行卡",
    ImageType.NORMAL: "普通图片",
    ImageType.DRIVERCARD: "驾驶证",
    ImageType.VEHICLECARD: "行驶证",
    ImageType.UNKNOWN: "未知类型",
}



# 二维码类型枚举
class QRCodeType:
    """二维码类型枚举"""
    WX_PAY = "WX_PAY"  # 微信支付
    WX_LOGIN = "WX_LOGIN"  # 微信登录
    WX_MINI = "WX_MINI"  # 微信小程序
    ALIPAY = "ALIPAY"  # 支付宝支付
    ALIPAY_MINI = "ALIPAY_MINI"  # 支付宝小程序
    UNION_PAY = "UNION_PAY"  # 云闪付
    BANK_PAY = "BANK_PAY"  # 银行支付
    WEIXIN = "WEIXIN"  # 微信
    DOUYIN = "DOUYIN"  # 抖音
    TAOBAO = "TAOBAO"  # 淘宝
    JD = "JD"  # 京东
    MEITUAN = "MEITUAN"  # 美团
    DIDI = "DIDI"  # 滴滴
    WIFI = "WIFI"  # WIFI
    VCARD = "VCARD"  # 名片
    TEL = "TEL"  # 电话
    SMS = "SMS"  # 短信
    EMAIL = "EMAIL"  # 邮件
    CALENDAR = "CALENDAR"  # 日历
    GEO = "GEO"  # 地理位置
    URL = "URL"  # 网址
    TEXT = "TEXT"  # 文本
    UNKNOWN = "UNKNOWN"  # 未知

# 二维码类型前缀映射
QR_TYPE_PREFIXES = {
    QRCodeType.WX_PAY: ["wxp://", "https://payapp.weixin.qq.com/", "weixin://wxpay/"],
    QRCodeType.WX_LOGIN: ["https://weixin.qq.com/w", "https://open.weixin.qq.com/"],
    QRCodeType.WX_MINI: ["wxaapp://", "https://wxaurl.cn/"],
    QRCodeType.ALIPAY: ["https://qr.alipay.com/", "alipays://platformapi/startapp", "https://mapi.alipay.com/"],
    QRCodeType.ALIPAY_MINI: ["alipays://platformapi/startapp?appId="],
    QRCodeType.UNION_PAY: ["unionpay://", "upapi://", "uppay://"],
    QRCodeType.BANK_PAY: ["icbc://", "ccb://", "abc://", "boc://", "cmb://"],
    QRCodeType.WEIXIN: ["weixin://"],
    QRCodeType.DOUYIN: ["snssdk1128://", "aweme://"],
    QRCodeType.TAOBAO: ["taobao://", "tbopen://"],
    QRCodeType.JD: ["openapp.jdmobile://", "jdmobile://"],
    QRCodeType.MEITUAN: ["meituanwaimai://", "imeituan://"],
    QRCodeType.DIDI: ["diditaxi://"],
    QRCodeType.WIFI: ["WIFI:"],
    QRCodeType.VCARD: ["BEGIN:VCARD", "MECARD:"],
    QRCodeType.TEL: ["tel:", "TEL:"],
    QRCodeType.SMS: ["sms:", "SMS:"],
    QRCodeType.EMAIL: ["mailto:", "MAILTO:"],
    QRCodeType.CALENDAR: ["BEGIN:VCALENDAR"],
    QRCodeType.GEO: ["geo:", "GEO:"],
    QRCodeType.URL: ["http://", "https://"],
}

# 二维码类型名称映射
QR_TYPE_NAMES = {
    QRCodeType.WX_PAY: "微信支付",
    QRCodeType.WX_LOGIN: "微信登录",
    QRCodeType.WX_MINI: "微信小程序",
    QRCodeType.ALIPAY: "支付宝支付",
    QRCodeType.ALIPAY_MINI: "支付宝小程序",
    QRCodeType.UNION_PAY: "云闪付",
    QRCodeType.BANK_PAY: "银行支付",
    QRCodeType.WEIXIN: "微信",
    QRCodeType.DOUYIN: "抖音",
    QRCodeType.TAOBAO: "淘宝",
    QRCodeType.JD: "京东",
    QRCodeType.MEITUAN: "美团",
    QRCodeType.DIDI: "滴滴",
    QRCodeType.WIFI: "WIFI",
    QRCodeType.VCARD: "名片",
    QRCodeType.TEL: "电话",
    QRCodeType.SMS: "短信",
    QRCodeType.EMAIL: "邮件",
    QRCodeType.CALENDAR: "日历",
    QRCodeType.GEO: "地理位置",
    QRCodeType.URL: "网址",
    QRCodeType.TEXT: "文本",
    QRCodeType.UNKNOWN: "未知",
}