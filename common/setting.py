import os
from enum import IntEnum
from typing import List

from common.jsonData import json_to_obj, obj_to_json
from common.logConstructor import logs
from common.tools import get_file_text, set_file_text


#图片颜色类型
class ImgColorType(IntEnum):
    """
    图片颜色类型
    """
    none=0
    RGB=1
    BGR=2
    def __init__(self, value):
        self._value_ = value
        # 定义中文标签
        data={0: '默认', 1: 'RGB', 2: 'BGR'}
        self._label_ = data[value]
    @property
    def label(self):
        return self._label_


#参数
class myParameter(object):

    def __init__(self, cfg, my_log=None):
        self.my_log:logs = my_log
        self.cfg = cfg

        self.run_pid_path=cfg['run_pid_path']
        self.user_path=cfg['user_path']
        self.default_user=cfg['default_user']
        self.default_password=cfg['default_password']
        self.default_save_path=cfg['default_save_path']
        self.default_show_image = cfg['default_show_image']

        self.default_manufacturer=cfg['default_manufacturer']
        self.default_fps=cfg['default_fps']
        self.default_auto_recording=cfg['default_auto_recording']

        self.is_start_sleep=cfg['is_start_sleep']==1#
        self.start_sleep_time=cfg['start_sleep_time']
        self.user_data=UserData()
        if os.path.exists(self.user_path):
            text = get_file_text(self.user_path)
            if text is not None and text!='':
                user_data=json_to_obj(text)
                if user_data is not None:
                    self.user_data.set_data(user_data)

        self.manufacturer=cfg['manufacturer']


        self.device_play_cfg=devicePlayCfg(cfg['device_play_cfg'])

        self.save_path_cfg=savePathCfg(cfg['save_path_cfg'])

    @property
    def get_user(self):
        if self.user_data.user is not None:
            return self.user_data.user
        return self.default_user
    @property
    def get_password(self):
        if self.user_data.password is not None:
            return self.user_data.password
        return self.default_password
    @property
    def get_save_path(self):
        if self.user_data.save_path is not None:
            return self.user_data.save_path
        return self.default_save_path
    @property
    def get_manufacturer(self):
        if self.user_data.manufacturer is not None:
            return self.user_data.manufacturer
        return self.default_manufacturer
    @property
    def get_auto_recording(self):
        if self.user_data.b_auto_recording is not None:
            return self.user_data.b_auto_recording
        return self.default_auto_recording

    @property
    def get_fps(self):
        if self.user_data.fps is not None:
            return self.user_data.fps
        return self.default_fps

    @property
    def get_show_image(self):
        if self.user_data.show_image is not None:
            return self.user_data.show_image
        return self.default_show_image

    def on_save_user(self,user,password,save_path,b_auto_recording,manufacturer,fps,b_show_image,list_camera):
        """

        :return:
        """
        data={
            "user": user,
            "password": password,
            "save_path": save_path,
            "manufacturer": manufacturer,
            "fps": fps,
            "show_image":b_show_image,
            "b_auto_recording": b_auto_recording,
            "list_camera": list_camera
        }

        set_file_text(self.user_path,obj_to_json(data,indent=1))

class CameraData(object):
    def __init__(self, cfg):
        self.ip=cfg['ip']
        self.manufacturer=cfg['manufacturer']
        self.state=cfg['state']
        self.b_show_image=cfg['b_show_image']
        self.b_save_recording=cfg['b_save_recording']
        self.user=cfg['user']
        self.password=cfg['password']
        self.fps=cfg['fps']

class UserData(object):
    def __init__(self):
        self.user = None
        self.password =None
        self.save_path = None
        self.manufacturer = None
        self.fps = None
        self.show_image= None
        self.list_camera: List[CameraData] = []
        self.b_auto_recording=False
    def set_data(self,cfg):
        self.user = cfg['user']
        self.password = cfg['password']
        self.save_path = cfg['save_path']
        self.manufacturer = cfg['manufacturer']
        self.fps = cfg['fps']
        self.show_image = cfg['show_image']
        list_camera = cfg['list_camera']
        if len(list_camera)>0:
            for item in list_camera:
                self.list_camera.append(CameraData(item))
        self.b_auto_recording = cfg['b_auto_recording'] if 'b_auto_recording' in cfg else False

# 摄像头运行状态
class CameraRunState(IntEnum):
    # 默认
    none = 0
    # 运行中
    run = 1
    # 已结束
    end = 2
    def __init__(self, value):
        self._value_ = value
        # 定义中文标签
        data={0: '默认', 1: '运行中', 2: '已结束'}
        self._label_ = data[value]
    @property
    def label(self):
        return self._label_

class devicePlayCfg(object):
    def __init__(self,cfg):

        self.is_image_RGB = cfg['is_image_RGB']==1

        self.is_max_size_limit = cfg['is_max_size_limit']==1
        self.where_max_size=cfg['where_max_size']
        if self.is_max_size_limit and self.where_max_size<=0:
            self.is_max_size_limit=False


        self.where_camera_queue_maxsize = cfg['where_camera_queue_maxsize']
        self.ffmpeg_log_level_input = cfg['ffmpeg_log_level_input']
        self.ffmpeg_log_level_output = cfg['ffmpeg_log_level_output']
        self.ffmpeg_hwaccel = cfg['ffmpeg_hwaccel']
        self.ffmpeg_vcodec = cfg['ffmpeg_vcodec']
        self.is_rk=cfg['is_rk']==1
        self.is_read_to_image=cfg['is_read_to_image']==1

        self.is_wait_state = cfg['is_wait_state'] == 1
        self.is_wait_time_by_fps = cfg['is_wait_time_by_fps'] == 1
        self.where_set_wait_time = cfg['where_set_wait_time']

        self.where_worker_image_show_interval = cfg['where_worker_image_show_interval']
        self.where_timeout=cfg['where_timeout']
        self.print_frame_time_interval = cfg['print_frame_time_interval']


class savePathCfg(object):
    def __init__(self,cfg):

        self.ffmpeg_log_level_input = cfg['ffmpeg_log_level_input']
        self.ffmpeg_log_level_output = cfg['ffmpeg_log_level_output']
        self.ffmpeg_codec = cfg['ffmpeg_codec']
        self.ffmpeg_bitrate = cfg['ffmpeg_bitrate']
        self.is_thread_writer_video=cfg['is_thread_writer_video']==1

#视频保存类
class CameraVideoWriterFFmpeg(object):
    def __init__(self,start_time,process,all_file_path,video_dir_path,video_name,str_date):


        self.end_state = False  # 结束状态

        self.process = process  # 视频保存类
        self.start_time = start_time  # 开始视频保存的时间

        self.actual_duration = 0  # 运动时长 秒

        self.all_file_path = all_file_path  # 视频保存路径
        self.video_dir_path=video_dir_path
        self.video_name=video_name
        self.str_date=str_date

        self.end_save_state=False#结束后保存状态
        self.writer_count=0#写入次数
        self.writer_time=0#最新写入时间

        self.video_duration=0#视频时长
        self.end_time = None  # 结束视频保存的时间
        self.str_end_time = None

    #时长
    def get_actual_duration(self,now_time):
        self.actual_duration= now_time-self.start_time
        return self.actual_duration

    #间隔
    def get_interval(self,now_time):
        return now_time-self.writer_time
