import concurrent.futures
import configparser
import hashlib
import json
import os
import threading
import time
import uuid
from datetime import datetime
import asyncio

import requests

from common.custom_exception import CustomException
from common.error_code import ErrorCode
from common.logger_config import logger
from common.result_utils import ResultDo
from db.taskdb import create_tables as create_task_tables, is_table_created as is_task_table_created, TaskMapper, \
    sync_table_structure as sync_task_table_structure
from apscheduler.schedulers.background import BackgroundScheduler
from connector.tweet_connector import TweetConnector, Segment as ISegment
from common.logger_config import logger
from db.taskdb import TaskMapper
import string_utils

from entity.task_status import Status
from processor.video_processor import Segment, VideoProcessor
from settings import PROJECT_ROOT

tweetConnector = TweetConnector()

taskMapper = TaskMapper()

config = configparser.ConfigParser()
config.read('./config.ini')

callback_thread_count = 1
video_processor_thread_count = 1

callbackThreadPool = concurrent.futures.ThreadPoolExecutor(max_workers=callback_thread_count)
videoThreadPool = concurrent.futures.ThreadPoolExecutor(max_workers=video_processor_thread_count)


def get_worker_id():
    mac_address = uuid.getnode()
    return ':'.join(['{:02x}'.format((mac_address >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])


def check_task(task):
    return string_utils.is_full_string(str(task.task_id)) and string_utils.is_full_string(task.title) \
        and string_utils.is_full_string(task.size) and string_utils.is_full_string(task.cover) \
        and string_utils.is_full_string(task.shots)


def fetch():
    tasks = tweetConnector.fetch(1)
    # for task in tasks:
    # if not check_task(task):
    #     logger.info(f"遇到无效任务,无视中...,task:{task}")
    #     return
    if len(tasks) == 0:
        return
    taskMapper.bulk_insert_tasks(tasks)
    pass


def _callback(task):
    logger.debug(f"Callback task")
    payload = {
        "task_id": task.task_id,
        "progress": task.progress,
        "status": task.status,
        "errcode": task.err_code,
        "errmsg": task.message,
        "video_url": task.video_url
    }
    try:
        tweetConnector.callback(payload)
    except CustomException as e:
        logger.warning(f"Callback task Warning:{e.message}")
        taskMapper.update_server_message(e.message, task.task_id)
        return
    except Exception as e:
        logger.exception(f"Callback task Fail", e)
        taskMapper.update_server_message(str(e), task.task_id)
        return
    taskMapper.set_synced_by_task_id(task.task_id)
    logger.debug(f"Callback task Success")


def callback():
    count = taskMapper.unsync_count()
    while count > 0:
        logger.debug(f"UnSync task count :{count}")
        task = taskMapper.find_unsync_task()
        if task is None:
            return
        _callback(task)
        time.sleep(2)


def download(url, _dir):
    # TODO test...
    def generate_hash_filename(content):
        """根据文件内容的哈希值生成文件名"""
        hash_value = hashlib.sha256(content).hexdigest()
        return hash_value.lower()

    work_dir = os.path.join(PROJECT_ROOT, _dir)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    work_dir = os.path.relpath(work_dir, PROJECT_ROOT)
    # 发送 GET 请求获取图片
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # 从 URL 中获取图片格式
            content_type = response.headers.get('content-type')
            image_extension = content_type.split('/')[-1]

            # 根据文件内容的哈希值生成文件名
            hash_filename = generate_hash_filename(response.content)
            filename = os.path.join(work_dir, f"{hash_filename}.{image_extension}")
            if os.path.exists(filename):
                return filename
            # 保存图片到本地
            with open(filename, 'wb') as f:
                f.write(response.content)
            logger.debug(f"downloaded successfully: {filename}")
            return filename
        else:
            logger.error(f"Failed to download from {url}: HTTP status code {response.status_code}")
    except Exception as e:
        logger.exception(f"Failed to download from {url}", e)
        raise CustomException(ErrorCode.TIME_OUT, str(e))


# 下载图片
def download_image(url):
    return download(url, 'resource/images')


def download_audio(url):
    return download(url, 'resource/audios')


def is_threadpool_idle(threadpool):
    thread_count = threadpool._max_workers
    # 获取线程池中的所有线程
    all_threads = threadpool._threads
    # 获取正在使用的线程数
    active_threads = sum(1 for thread in all_threads if thread.is_alive())
    message = f"总线程数:{thread_count},活跃线程数:{active_threads}"
    if active_threads >= thread_count:
        message = message + ',线程池忙碌中...'
    else:
        message = message + ',有可用线程...'
    logger.debug(message)
    return active_threads < thread_count


def run_task(task):
    logger.debug(f"【{task.task_id}】Execute task start")

    try:
        json_data = json.loads(task.shots)
        segments = [Segment(segment_data['text'], segment_data['image_path'], segment_data['audio_path']) for
                    segment_data in
                    json_data]
        # 创建新的事件循环
        new_loop = asyncio.new_event_loop()

        # 将新的事件循环设置为当前线程的事件循环
        asyncio.set_event_loop(new_loop)
        if task.size is not None:
            size = task.size.split("*")
            if len(size) != 2:
                width = size[0]
                height = size[0]
            else:
                width = size[0]
                height = size[1]

            width = int(width)
            height = int(height)
        else:
            width = None
            height = None
        # 同步调用 run_task 函数
        video_path = new_loop.run_until_complete(
            VideoProcessor(segments=segments, task_id=task.task_id, width=width, height=height).run())
    except CustomException as e:
        logger.error(f"【{task.task_id}】Execute task end,error:{e.message}")
        return ResultDo(e.code, e.message)
    except Exception as e:
        logger.exception(f"【{task.task_id}】Execute task end,error:", e)
        return ResultDo(ErrorCode.TIME_OUT, 'Video generation timed out.')
    logger.debug(f"【{task.task_id}】Execute task end")
    return ResultDo(code=ErrorCode.OK, data=video_path)


def execute_task():
    def execute_task_func(task):
        try:
            if not check_task(task):
                logger.info(f"遇到无效任务,删除中...,task:{task}")
                taskMapper.remove(task.id)
                return
            shots = task.shots
            json_data = json.loads(shots)
            segments = [ISegment(**segment_data) for segment_data in json_data]
            for segment in segments:
                if not string_utils.is_full_string(segment.image_path):
                    segment.image_path = download_image(segment.image_url)
                if not string_utils.is_full_string(segment.audio_path):
                    segment.audio_path = download_audio(segment.audio_url)
            serialized_segments = [segment.segment_to_dict() for segment in segments]
            shots = json.dumps(serialized_segments)
            task.shots = shots
            taskMapper.update_shots(shots, task.task_id)
        except CustomException as e:
            taskMapper.set_fail(task.task_id, e.code, e.message)
            return
        except Exception as e:
            logger.exception(e)
            taskMapper.set_fail(task.task_id, ErrorCode.UNKNOWN, str(e))
            return

        try:
            # 将任务设置成执行中
            task.status = Status.DOING.value
            taskMapper.set_status(task.task_id, task.status)
            logger.debug(f"将task设置为doing状态,task_id:{task.task_id}")
            _callback(task)

            execute_result = run_task(task)

            if execute_result.code == 0:
                # 成功
                task.status = Status.SUCCESS.value
                task.video_path = execute_result.data
                taskMapper.set_success(task.task_id, video_path=execute_result.data)
                _callback(task)
            elif execute_result.code == ErrorCode.TASK_COMPLETED:
                # 任务已完成，什么都不需要做
                pass
            else:
                # 失败
                task.status = Status.FAIL.value
                task.message = execute_result.message
                task.err_code = execute_result.code
                taskMapper.set_fail(task.task_id, execute_result.code, execute_result.message)
                _callback(task)
        except CustomException as e:
            raise e
        except Exception as e:
            logger.exception(e)
            raise e

    tasks = taskMapper.get_executable_tasks(video_processor_thread_count)
    if len(tasks) == 0:
        logger.info('All tasks have been completed!!!')
    for _task in tasks:
        is_threadpool_idle(videoThreadPool)
        taskMapper.set_status(_task.task_id, Status.DOING.value)
        videoThreadPool.submit(execute_task_func, _task)
        time.sleep(10)


def main():
    logger.info("初始化中...")
    logger.info(f"当前worker_id:{get_worker_id()}")
    # 在项目第一次启动时创建表
    if not is_task_table_created():
        create_task_tables()

    sync_task_table_structure()
    scheduler = BackgroundScheduler()
    # scheduler.add_job(fetch, 'interval', seconds=1, next_run_time=datetime.now())
    # scheduler.add_job(callback, 'interval', seconds=10, next_run_time=datetime.now())
    scheduler.add_job(execute_task, 'interval', seconds=60, next_run_time=datetime.now())
    scheduler.start()
    event = threading.Event()

    event.wait()


if __name__ == "__main__":
    main()
