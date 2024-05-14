# 使用官方 Python 镜像作为基础镜像
FROM python:3.8

# 设置工作目录
WORKDIR /app

# 将项目代码添加到容器中
COPY . /app

RUN apt-get update
RUN apt-get install -y nload
RUN apt-get install -y htop
RUN apt-get install -y wget


# 安装项目依赖(国外服务器可去掉-i)
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.5/dumb-init_1.2.5_x86_64
RUN chmod +x /usr/local/bin/dumb-init

# 设置启动命令
CMD ["dumb-init","python", "app.py"]
