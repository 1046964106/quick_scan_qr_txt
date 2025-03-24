## 使用说明

QuickScan_QR_TXT是一个基于ZBar库和paddleOCR的Python应用程序，用于识别二维码。它可以识别本地图像、网络图像和Base64编码的图像，可识别身份证，银行卡，行驶证，驾驶证等,并提供HTTP服务API。


### 1. 安装依赖
1. 安装Python 3.x版本。
2. 安装必要的Python库：

   ```plaintext
   FROM python:3.9-slim
   WORKDIR /app

   # 安装系统依赖
   RUN apt-get update && apt-get install -y \
      libzbar0 \
      libgl1-mesa-glx \
      libglib2.0-0 \
      && rm -rf /var/lib/apt/lists/*

   # 复制项目文件
   COPY . /app/

   # 安装Python依赖
   RUN pip install --no-cache-dir -r requirements.txt

   # 暴露端口（如果你的应用是Web服务）
   EXPOSE 5000

   # 启动应用
   CMD ["python", "app.py"]
      
   ```

### 2. 运行应用
### 在Linux系统上创建虚拟环境并安装依赖：
 ```plaintext
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   ```
###  运行应用：
 ```plaintext
    python app.py server 
    python app.py server 8080
    python app.py server 8080 192.168.1.1
```
### 3. 命令行使用
1. 识别本地图像：
   
   ```plaintext
   python app.py.py e:\WORK_SHOW\python\download_log\qr_show\test.jpg
   ```
2. 识别网络图像：
   
   ```plaintext
   python app.py.py https://example.com/image.jpg
    ```
3. 识别Base64编码图像：
   
   ```plaintext
   python app.py.py base64:iVBORw0KGgoAAAANSUhEUgAA...
    ```
4. 启动HTTP服务：
   
   ```plaintext
   python app.py.py server 5000 127.0.0.1
    ```
### 4. HTTP服务API
启动服务后，可以通过以下方式调用API：

1. 处理网络图片：
   
   ```plaintext
   POST /recognize
   Content-Type: application/x-www-form-urlencoded
   
   image_url=https://example.com/image.jpg
    ```
2. 处理Base64图片：
   
   ```plaintext
   POST /recognize
   Content-Type: application/x-www-form-urlencoded
   
   image_base64=iVBORw0KGgoAAAANSUhEUgAA...
    ```
3. 处理本地图片路径(服务器的绝对路径)：
   
   ```plaintext
   POST /recognize
   Content-Type: application/x-www-form-urlencoded
   
   image_path=e:\WORK_SHOW\python\download_log\qr_show\test.jpg
   ```
4. 上传图片文件：
   
   ```plaintext
   POST /recognize
   Content-Type: multipart/form-data
   
   image=@本地图片文件
    ```