# 推文工具
## 概述
> 该工具是闲鱼买家要求做的工具，主要目的是根据大模型生成的图片、文本音频，批量合成推流视频，根据这个思路，结合小说爬虫项目，可以批量生成推流视频，所谓的印钞机应该就是这样来的吧。核心代码在processor中，由于接入的是对方的任务队列，所以无法直接使用，开源出来也是为了给大家借鉴推流工具思路，如果这个项目能帮到你的话，就点个starts呗。
## docker部署:

```shell
docker build -t runway .
docker run runway 
```

## 普通部署

1. 安装依赖

```shell
pip install -r requirements.txt
```

2. 配置服务器url，访问密钥

```shell
config.ini中的如下配置
[DIAN_BAOBAO]
partner_id = xxx
private_key = xxx
base_url = https://xxx.com

[ALI_YUN]
access_key_id = LTAI5tJPvB78DmEYUg4mxTdS
access_key_secret = D0sMUyiYhkznCjOi5jG8B1uOebzoDu
bucket_name = dbb-aigc-result
endpoint = http://oss-cn-shanghai.aliyuncs.com
directory= works
oss_url = https://aigcresult.di6dai.com
```

3. 根据服务器配置调整并发数

```shell
config.ini中的如下配置
[SERVICE]
callback_max_thread_count = 1 # 回调接口线程池大小
video_processor_count = 8 # 视频生成线程池大小
```

4. 执行启动程序

```shell
python app.py
```
