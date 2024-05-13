import json
import os.path
import random
import asyncio
import secrets
import string
from PIL import Image

import numpy as np
from moviepy.audio.AudioClip import AudioClip, CompositeAudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import TextClip, ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx import resize
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
import moviepy.video.fx.all as vfx
from numpy import array

from processor.txt_audio_processor import TxtAudioProcessor
from settings import PROJECT_ROOT


class VideoProcessor:
    def __init__(self, segments: list, task_id: str = None, height: int = None, width: int = None):
        self.segments = segments
        self.speed = 12
        self.task_id = task_id
        self.height = height
        self.width = width

    @staticmethod
    def __to_videos(audio_clip, txt, image_clip):
        # TODO 一个画面对应一段语音
        # TODO 将每段画面配上每段的字幕
        pass

    # 图片列表 从上到下滚动
    # 控制视频上下滑动

    def fl_up(self, height, width, gf, t):
        speed = self.speed
        height = height
        size = int((height * 0.7) // 1)  # 1152

        image = gf(t)
        start_index = int(speed * t)  # 0
        end_index = int(speed * t) + size  # 1152
        if end_index > height:
            end_index = height
            start_index = height - size
        # cropped_image = image[start_index:end_index, :]
        cropped_image = image[start_index:end_index, :]
        return cropped_image

    def fl_down(self, height, width, gf, t):
        speed = self.speed
        size = int((height * 0.8) // 1)  # 根据图像高度计算裁剪尺寸

        image = gf(t)
        start_index = max(0, height - int(speed * t) - size)  # 起始位置随时间和速度变化
        end_index = min(height, height - int(speed * t))  # 结束位置随时间和速度变化，同时不超过图像高度

        # 截取图像的垂直范围，水平方向不变
        cropped_image = image[start_index:end_index, :]

        return cropped_image

    # 控制视频从右下角到左上角滑动
    def fl_right_down(self, gf, t):
        speed = self.speed
        size = 700
        image = gf(t)
        start_index_x = min(768 - size, int(speed * t))  # 起始位置不大于(768-size)
        end_index_x = min(768, int(speed * t) + size)  # 结束位置不大于768
        start_index_y = min(768 - size, int(speed * t))  # 起始位置不大于(768-size)
        end_index_y = min(768, int(speed * t) + size)  # 结束位置不大于768
        cropped_image = image[start_index_y:end_index_y, start_index_x:end_index_x]
        return cropped_image

    # 控制视频从左上角到右下角斜向滑动
    def fl_left_up(self, gf, t):
        speed = self.speed
        size = 700
        image = gf(t)
        start_index_x = max(0, 768 - int(speed * t) - size)  # 起始位置不小于0
        end_index_x = min(768, 768 - int(speed * t))  # 结束位置不大于768
        start_index_y = max(0, 768 - int(speed * t) - size)  # 起始位置不小于0
        end_index_y = min(768, 768 - int(speed * t))  # 结束位置不大于768
        cropped_image = image[start_index_y:end_index_y, start_index_x:end_index_x]
        return cropped_image

    # 控制视频从左下到右上
    def fl_left_down(self, gf, t):
        speed = self.speed
        size = 700
        image = gf(t)
        start_index_x = max(0, 768 - int(speed * t) - size)  # 起始位置不小于0
        end_index_x = min(768, 768 - int(speed * t))  # 结束位置不大于768
        start_index_y = min(768 - size, int(speed * t))  # 起始位置不大于(768-size)
        end_index_y = min(768, int(speed * t) + size)  # 结束位置不大于768
        cropped_image = image[start_index_y:end_index_y, start_index_x:end_index_x]
        return cropped_image

    # 控制视频从右上角到左下角斜向滑动
    def fl_right_up(self, gf, t):
        speed = self.speed
        size = 700
        image = gf(t)
        start_index_x = min(768 - size, int(speed * t))  # 起始位置不大于(768-size)
        end_index_x = min(768, int(speed * t) + size)  # 结束位置不大于768
        start_index_y = max(0, 768 - int(speed * t) - size)  # 起始位置不小于0
        end_index_y = min(768, 768 - int(speed * t))  # 结束位置不大于768
        cropped_image = image[start_index_y:end_index_y, start_index_x:end_index_x]
        return cropped_image

    @staticmethod
    def generate_random_string(length=32):
        alphabet = string.ascii_lowercase
        return ''.join(secrets.choice(alphabet) for i in range(length))

    async def run(self):
        clips = []
        _fls = [self.fl_up, self.fl_down]
        # 获取图片最大宽度和高度
        images = []
        for segment in self.segments:
            images.append(Image.open(segment.image_path))
        if self.width is None and self.height is None:
            max_width, max_height = array([im.size for im in images]).max(axis=0)
        else:
            max_width, max_height = (self.width, self.height)

        for index, segment in enumerate(self.segments):
            # 统一裁剪图片
            im = Image.new('RGB', (max_width, max_height), (160, 160, 160))
            left = (max_width - images[index].width) // 2
            upper = (max_height - images[index].height) // 2
            im.paste(images[index], (left, upper))

            if self.task_id is None:
                _fl = _fls[index % 2]
            else:
                _fl = _fls[random.randint(0, len(_fls) - 1)]
            print("开始处理音频", _fl)
            if segment.audio_path is None:
                audio_clip = await self.txt_to_voice(segment)
            else:
                audio_clip = AudioFileClip(segment.audio_path)
            print("音频处理成功")
            print(f"开始处理图片{segment.image_path}")

            # img_clip = ImageSequenceClip([segment.image_path], fps=audio_clip.fps)
            img_clip = ImageClip(array(im))
            # 调整图片尺寸
            width = img_clip.size[0]
            height = img_clip.size[1]

            img_clip = img_clip.set_duration(audio_clip.duration + 0.1) \
                .fl(lambda gf, t: _fl(height, width, gf, t), apply_to=['mask'])

            # TODO 将字幕text加到这个图片视频audio_clip中
            # Create text clip with the subtitle
            font_url = PROJECT_ROOT + '/resource/HiraginoSansGB.ttc'

            # 计算字母距离底部位置
            bottom_margin = 50
            subtitle_height = 24
            video_height = img_clip.size[1]
            y_pos = video_height - bottom_margin - subtitle_height

            txt_clip = TextClip(segment.text, fontsize=20, color='white', font=font_url) \
                .set_position(('center', y_pos)).set_duration(audio_clip.duration)
            composite_clip = CompositeVideoClip([img_clip, txt_clip])

            clip = composite_clip.set_audio(audio_clip)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips)

        if self.task_id is not None:
            video_path = 'resource/videos/' + str(self.task_id) + '.mp4'
        else:
            video_path = "resource/videos/" + self.generate_random_string() + ".mp4"
        result = os.path.join(PROJECT_ROOT, video_path)
        final_clip.write_videofile(result, fps=24, audio_codec='aac')
        return video_path

    @staticmethod
    async def txt_to_voice(segment):
        voices = [
            {"name": "zh-TW-HsiaoChenNeural", "gender": "Female"},
            {"name": "zh-TW-HsiaoYuNeural", "gender": "Female"},
            {"name": "zh-TW-YunJheNeural", "gender": "Male"},
            # {"name": "zh-HK-HiuGaaiNeural", "gender": "Female"},
            # {"name": "zh-HK-HiuMaanNeural", "gender": "Female"},
            # {"name": "zh-HK-WanLungNeural", "gender": "Male"},
            {"name": "zh-CN-XiaoxiaoNeural", "gender": "Female"},
            {"name": "zh-CN-XiaoyiNeural", "gender": "Female"},
            {"name": "zh-CN-YunjianNeural", "gender": "Male"},
            {"name": "zh-CN-YunxiNeural", "gender": "Male"},
            {"name": "zh-CN-YunxiaNeural", "gender": "Male"},
            {"name": "zh-CN-YunyangNeural", "gender": "Male"},
            {"name": "zh-CN-liaoning-XiaobeiNeural", "gender": "Female"},
            {"name": "zh-CN-shaanxi-XiaoniNeural", "gender": "Female"}
        ]
        # _voice = voices[random.randint(0, len(voices) - 1)]['name']
        # print(_voice)
        _voice = 'zh-CN-YunxiNeural'
        audio_clip = await TxtAudioProcessor(segment.text, _voice, segment.speed).run(
            # PROJECT_ROOT + '/resource/audio/' + str(index) + ".mp3"
        )
        return audio_clip


class Segment:

    def __init__(self, _text: str, image_path: str, audio_path: str = None, speed: int = 1):
        self.image_path = image_path
        self.audio_path = audio_path
        self.text = _text
        self.speed = speed


def main():
    data = [{
        'image_path': '/Users/watermelon/workspace/auto-video/resource/images/4a193dfc7a32a249583fa85ebc71a4552261ca3ac6535d2394adf93f9bda802a.png',
        'text': '大壮，是一只流浪猫，他非常饥饿的走在街头。',
        'speed': 1
    }]

    _seg = json.dumps(data)
    json_data = json.loads(_seg)
    segments = [Segment(_text=segment_data['text'], image_path=segment_data['image_path']) for segment_data in
                json_data]
    return VideoProcessor(segments, None, height=720, width=720).run()


if __name__ == "__main__":
    asyncio.run(main())
