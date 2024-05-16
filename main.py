import asyncio
import json

from processor.video_processor import VideoProcessor, Segment


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
