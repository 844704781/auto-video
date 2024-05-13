from common.logger_config import logger
from connector.base_connector import BaseConnector
from common.custom_exception import CustomException


class TweetConnector(BaseConnector):

    def fetch(self, num):
        """
        {
            "num": 1
        }
        :param payload:
        :return:
        [
            {
                "task_id": "1", //任务ID
                "title": "初露锋芒", //作品标题
                "size": "720*720", //视频尺寸
                "cover": "https://dbb-aigc-result.oss-accelerate.aliyuncs.com/Uploads/works/audio/cover.png", //视频封面
                "shots": "[{\"text\":\"这个少年是让他老爹都害怕的存在\",\"image_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/01.jpg\",\"audio_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/1\\/01.wav\",\"speed\":1},{\"text\":\"年仅13岁就已是一身健子肉\",\"image_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/02.jpg\",\"audio_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/1\\/02.wav\",\"speed\":1},{\"text\":\"一拳可以锤死一头小母牛的那种\",\"image_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/03.png\",\"audio_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/1\\/03.wav\",\"speed\":1},{\"text\":\"他本是300年前永动魔王的勇士\",\"image_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/01.jpg\",\"audio_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/1\\/04.wav\",\"speed\":1},{\"text\":\"为救好兄弟搭上了自己的小命\",\"image_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/01.jpg\",\"audio_url\":\"https:\\/\\/dbb-aigc-result.oss-accelerate.aliyuncs.com\\/Uploads\\/works\\/audio\\/1\\/05.wav\",\"speed\":1}]" //分镜头Json字符串（请转json）
            }
        ]
        """
        payload = {
            "num": num
        }
        uri = '/openapi/job/works/fetch'
        resp = self.post(uri, payload)
        if resp.get('code') != 0:
            raise CustomException(resp.get('code'), resp.get('message'))
        return resp.get('data')

    def callback(self, payload):
        """
        {
            "code": 0,
            "message": "操作成功OK",
            "data": null,
            "isSuccess": true
        }
        :param payload:
        :return:
        """
        uri = '/openapi/job/works/callback'
        resp = self.post(uri, payload)
        if resp.get('code') != 0:
            raise CustomException(resp.get('code'), resp.get('message'))
        return resp.get('data')


class Segment:
    def __init__(self, text: str, speed: int, image_path: str = None, image_url: str = None, audio_url: str = None,
                 audio_path: str = None):
        self.image_path = image_path
        self.image_url = image_url
        self.audio_url = audio_url
        self.audio_path = audio_path
        self.text = text
        self.speed = speed

    def segment_to_dict(self):
        return {
            "image_path": self.image_path,
            "image_url": self.image_url,
            "audio_url": self.audio_url,
            "audio_path": self.audio_path,
            "text": self.text,
            "speed": self.speed
        }
