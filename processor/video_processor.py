import json
import os.path
import random
import asyncio
import secrets
import string

import numpy as np
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
import moviepy.video.fx.all as vfx
from processor.txt_audio_processor import TxtAudioProcessor
from settings import PROJECT_ROOT


class VideoProcessor:
    def __init__(self, segments: list, task_id: str = None):
        self.segments = segments
        self.speed = 12
        self.task_id = task_id

    @staticmethod
    def __to_videos(audio_clip, txt, image_clip):
        # TODO 一个画面对应一段语音
        # TODO 将每段画面配上每段的字幕
        pass

    # 图片列表 从上到下滚动
    # 控制视频上下滑动
    def _fl_up(self, get_frame, t):
        speed = self.speed
        size = 700
        image = get_frame(t)
        print(image)
        start_index_y = max(0, 768 - int(speed * t) - size)  # 起始位置不小于0
        end_index_y = min(768, 768 - int(speed * t))  # 结束位置不大于768
        cropped_image = image[start_index_y:end_index_y, :]
        return cropped_image

    def fl_up(self, height, weight, duration, gf, t):
        speed = self.speed
        size = 1024
        image = gf(t)
        start_index_y = max(0, height - int(speed * t) - size)  # 起始位置不小于0
        end_index_y = min(height, height - int(speed * t))  # 结束位置不大于视频高度
        start_index_x = min(weight - size, int(weight / 2) - size // 2)  # X轴居中
        end_index_x = min(weight, int(weight / 2) + size // 2)  # X轴居中
        cropped_image = image[start_index_y:end_index_y, start_index_x:end_index_x]
        return cropped_image

    # def fl_down(self, gf, t):
    #     speed = self.speed
    #     size = 700  # 裁剪后的图像高度
    #     image = gf(t)  # 获取原始图像
    #     start_index = int(speed * t)  # 计算滚动的起始索引
    #     end_index = start_index + size  # 计算滚动的结束索引
    #     if start_index < 0:  # 如果滚动超出了图像的顶部，则调整起始索引和结束索引
    #         start_index = 0
    #         end_index = size
    #     if end_index > image.shape[0]:  # 如果滚动超出了图像的底部，则调整结束索引和起始索引
    #         end_index = image.shape[0]
    #         start_index = end_index - size
    #     cropped_image = image[start_index:end_index, :]  # 裁剪图像
    #     return cropped_image

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
        if self.task_id:
            _fls = [self.fl_up, self.fl_up]
        else:
            _fls = [self.fl_left_up, self.fl_left_down, self.fl_right_up, self.fl_right_down, self.fl_left_up]
        for index, segment in enumerate(self.segments):
            if self.task_id:
                _fl = _fls[index % 2]
            else:
                _fl = _fls[random.randint(0, len(_fls) - 1)]
            print("开始处理音频")
            if segment.audio_path is None:
                audio_clip = await self.txt_to_voice(segment)
            else:
                audio_clip = AudioFileClip(segment.audio_path)
            print("音频处理成功")
            img_clip = ImageSequenceClip([segment.image_path], fps=audio_clip.fps)

            img_clip = img_clip.set_duration(audio_clip.duration) \
                .fl(_fl, apply_to=['mask'])
            # TODO 将字幕text加到这个图片视频audio_clip中
            # Create text clip with the subtitle
            font_url = PROJECT_ROOT + '/resource/HiraginoSansGB.ttc'

            # 计算字母距离底部位置
            bottom_margin = 50
            subtitle_height = 24
            video_height = img_clip.size[1]
            y_pos = video_height - bottom_margin - subtitle_height

            txt_clip = TextClip(segment.text, fontsize=24, color='white', font=font_url) \
                .set_position(('center', y_pos)).set_duration(audio_clip.duration)
            composite_clip = CompositeVideoClip([img_clip, txt_clip])

            clip = composite_clip.set_audio(audio_clip)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips)

        if self.task_id:
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
        _voice = voices[random.randint(0, len(voices) - 1)]['name']
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
        'image_path': '/Users/watermelon/workspace/auto-video/resource/images/1.jpg',
        'text': '在一个风和日丽的早晨，小猫咪Mimi在花园中追逐蝴蝶。',
        'speed': 1
    },
        {
            'image_path': '/Users/watermelon/workspace/auto-video/resource/images/2.jpg',
            'text': '它一不小心跳进了一个装满五颜六色花朵的花篮里。',
            'speed': 1
        }, {
            'image_path': '/Users/watermelon/workspace/auto-video/resource/images/3.jpg',
            'text': '当Mimi从花篮中跳出来时，它的身上沾满了花瓣。',
            'speed': 1
        }, {
            'image_path': '/Users/watermelon/workspace/auto-video/resource/images/4.jpg',
            'text': '它高兴地跑向家门口，留下一路花瓣的足迹。',
            'speed': 1
        }, {
            'image_path': '/Users/watermelon/workspace/auto-video/resource/images/5.jpg',
            'text': '最终，Mimi在自家门口滚成一团，打了个满足的小盹。',
            'speed': 1
        }
    ]

    _seg = json.dumps(data)
    json_data = json.loads(_seg)
    segments = [Segment(_text=segment_data['text'], image_path=segment_data['image_path']) for segment_data in
                json_data]
    return VideoProcessor(segments).run()


if __name__ == "__main__":
    asyncio.run(main())
