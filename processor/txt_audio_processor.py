import tempfile
from gtts import gTTS
from moviepy.audio.io.AudioFileClip import AudioFileClip
import edge_tts


class TxtAudioProcessor:
    def __init__(self, txt, voice: str = 'zh-CN-XiaoyiNeural', speed: int = 1):
        self.txt = txt
        self.speed = speed
        self.voice = voice
        pass

    @staticmethod
    def __modify_audio_speed(audio_clip, speed):
        new_au = audio_clip.fl_time(lambda t: speed * t, apply_to=['mask', 'audio'])  # 1.1表示调整速度
        new_au = new_au.set_duration(audio_clip.duration / speed)  # 1.1表示调整速度
        return new_au

    @staticmethod
    def engine_gtts(txt):
        tts = gTTS(txt, lang='zh')
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_filename = temp_file.name
            tts.write_to_fp(temp_file)

        return temp_filename

    @staticmethod
    async def edge_tts(voice, txt):
        temp_filename = None
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_filename = temp_file.name
            communicate = edge_tts.Communicate(txt, voice, rate='+0%')
            await communicate.save(temp_filename)
            return temp_filename
        finally:
            if temp_filename:
                temp_file.close()

    # 得到一个音频对象
    async def run(self, file: str = None):
        temp_filename = await self.edge_tts(self.voice, self.txt)
        # Load the audio file with MoviePy
        audio_clip = AudioFileClip(temp_filename)

        modified_audio_clip = self.__modify_audio_speed(audio_clip, self.speed)
        if file:
            # Save the modified audio clip
            modified_audio_clip.write_audiofile(file, codec='mp3')

        return modified_audio_clip
