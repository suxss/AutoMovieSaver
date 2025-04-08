# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 首先复制 requirements.txt，以便利用 Docker 的缓存机制
COPY requirements.txt .

# 安装依赖库
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件到容器中
COPY . /app/

# 设置时区为亚洲/上海
ENV TZ=Asia/Shanghai

# 运行 Python 程序
CMD ["python", "main.py"]