import platform
import threading

import traceback
from enum import IntEnum

import cv2
import time


import ffmpeg
import numpy as np
import os
from threading import Thread

from common.queueManage import QueueManage
from common.setting import ImgColorType
from common.tools import is_ip_reachable, cv_imread_CN, kill_process, get_str_time



#帧数据类型
class FrameDataType(IntEnum):
    bytes=1
    image=2

#帧图片数据
class FrameImage(object):

    def __init__(self,state=False,img=None,msg='',frame_time=0,img_color_type:ImgColorType=ImgColorType.none,remaining_count:int=0):
        """
        帧图片数据
        :param state: 状态
        :param img: 图片
        :param msg: 描述
        :param frame_time: 时间
        :param img_color_type: 图片颜色
        :param remaining_count: 剩余数量
        """
        self.state= state
        self.img= img
        self.msg= msg
        self.frame_time=frame_time
        self.img_color_type = img_color_type  # 图片颜色类型
        self.remaining_count=remaining_count



#帧数据
class FrameData(object):

    def __init__(self, t, frame_data_type, data,frame_count,img_h=0,img_w=0,str_time='',img_color_type:ImgColorType=ImgColorType.BGR):
        self.frame_time = t #时间
        self.type = frame_data_type #类型
        self.data = data#数据
        self.frame_count=frame_count#帧
        self.img_h=img_h#图片高度
        self.img_w =img_w#图片宽度
        self.str_time=str_time#字符串时间
        self.img_color_type=img_color_type#图片颜色类型


    def get_img(self):
        if self.type == FrameDataType.image:
            return self.data
        img=None
        try:
            img = np.frombuffer(self.data, np.uint8).reshape([self.img_h, self.img_w, 3])#.copy()
            self.type=FrameDataType.image#只要转换一次就好了
            self.data=img
        except Exception as ex:
            traceback.print_exc()
            print('转换图片失败：',ex)
        return img

    def __str__(self):
        return "FrameData(type={},frame_count={},data={},time={})".format(self.type,self.frame_count,len(self.data),self.str_time)


#流加载管理器 基类
class Load_camera_stream(object):
    def __init__(self, num=0, camera_rtsp='',b_rgb=False,output_fps=None,ip='',where_timeout=5,
                 where_camera_queue_maxsize=30,is_wait_state=False,
                 is_wait_time_by_fps=False,where_set_wait_time=0,
                 is_max_size_limit=False,where_max_size=None):
        """
        流加载管理器 基类
        Args:
            num: 序号
            camera_rtsp: rtsp地址
            b_rgb: 转rgb
            output_fps: 输出fps
            ip: 设备IP
            where_timeout: 超时自动断开时间（秒）
            where_camera_queue_maxsize: 10 队列最大缓存的数量
            is_wait_state: 启用每张图片的，等待时间状态
            is_wait_time_by_fps: 每张图片的，等待时间自动根据fps来计算
            where_set_wait_time: 设置的每张图片的，等待时间 毫秒
        """
        self.num=num#序号
        self.camera_rtsp=camera_rtsp#rtsp地址
        self.b_rgb:bool=b_rgb#转 rgb
        self.b_release = False#释放状态
        self.b_release_count = 0#释放次数
        self.load_camera_state = False#初始化摄像头的状态
        self.get_last_img_count=0#记录调用获取图片的次数
        self.get_last_img_time=''#记录最新获取的图片的时间

        self.get_w = None#图片宽度
        self.get_h = None#图片高度
        self.get_max_size = None#图片最大尺寸

        self.read_count=0#读取图片次数
        self.frame_count=0#视频帧
        self.get_str_img_time = ''#获取图片的时间 字符串
        self.get_float_img_time = 0#获取图片的时间 时间戳
        self.where_discard_count = 25  # 前面10张图片不要，是绿屏的
        self.discard_count = 0#连续丢弃图片次数
        self.output_fps=output_fps#设置的输出fps
        self.play_fps=None#记录播放的fps
        self.ip=ip#ip地址
        self.where_ping_count= 5#ping ip次数
        self.where_out_count = 100  # 断开次数
        self.error_count=0#累计连续错误次数
        self.where_timeout=where_timeout#超时自动断开时间，秒
        self.where_camera_queue_maxsize = where_camera_queue_maxsize #队列最大缓存的数量

        self.my_frame_queue=QueueManage(maxsize=self.where_camera_queue_maxsize)#原始数据的队列

        self.is_wait_state=is_wait_state #启用每张图片的，等待时间状态
        self.is_wait_time_by_fps=is_wait_time_by_fps #每张图片的，等待时间自动根据fps来计算
        self.where_auto_wait_time=0#自动计算的每张图片的，等待时间 毫秒
        self.where_set_wait_time=where_set_wait_time#设置的每张图片的，等待时间 毫秒
        self.where_wait_time=0#每张图片的，等待时间 毫秒，where_auto_wait_time+where_set_wait_time 推理出来的


        self.is_max_size_limit=is_max_size_limit
        self.where_max_size=where_max_size

    #重置数据
    def on_reset_data(self):
        self.read_count=0#读取图片次数
        self.frame_count=0#视频帧
        if self.my_frame_queue.count>0:
            self.my_frame_queue.clear()

    #释放内存
    def release_cap(self):
        pass

    #获取图片
    def get_last_img(self)->FrameImage:
        """
        获取帧图片
        :return:  FrameImage
        """
        self.get_last_img_count += 1
        frame_image=FrameImage()

        if self.b_release is True:
            frame_image.msg='已经关闭释放'
            return frame_image#已经退出

        if self.where_timeout > 0 and self.get_float_img_time>0:
            # 判断是否已经太久没有更新图片了
            now_time = time.time()
            interval_time = now_time - self.get_float_img_time
            if interval_time > self.where_timeout:
                self.release_cap()
                frame_image.msg = '已经超时，没有数据返回'
                return frame_image  # 不能重复获取

        is_null=self.my_frame_queue.is_null
        if is_null is True:
            frame_image.msg = '图片为空'
            return frame_image

        # if self.get_last_img_time!='' and self.get_last_img_time==self.get_str_img_time:
        #     msg = '不能重复获取图片'
        #     print(msg)
        #     return frame_image#不能重复获取

        self.get_last_img_time=self.get_str_img_time

        state, value, msg = self.my_frame_queue.get()
        if state is False:
            frame_image.msg = '图片为空'
            return frame_image
        frame_image.img_color_type=value.img_color_type
        img=value.get_img()#获取数据
        if img is None:
            frame_image.msg = '图片为空'
            return frame_image
        frame_image.img=img
        frame_image.frame_time=value.frame_time#时间
        frame_image.state=True
        frame_image.remaining_count = self.my_frame_queue.count

        return frame_image

    #获取播放的 fps
    def get_play_fps(self):
        return self.play_fps

# 流加载管理器 ffmpeg
class Load_camera_stream_to_ffmpeg(Load_camera_stream):  # 加载摄像头流
    def __init__(self, num=0,camera_rtsp='', b_rgb=False,loglevel_input='warning',
                 output_loglevel='warning',output_fps=None, ip='',is_ping=False,where_timeout=5,where_camera_queue_maxsize=10,is_wait_state=False,
                 is_wait_time_by_fps=False,where_set_wait_time=0,ffmpeg_hwaccel='',ffmpeg_vcodec='',is_rk=False,is_read_to_image=False,is_max_size_limit=False,where_max_size=None):
        super().__init__(num,camera_rtsp,b_rgb,output_fps,ip,where_timeout,where_camera_queue_maxsize,is_wait_state,is_wait_time_by_fps,where_set_wait_time,is_max_size_limit,where_max_size)
        self.ffmpeg_hwaccel=ffmpeg_hwaccel
        self.ffmpeg_vcodec=ffmpeg_vcodec
        self.is_rk = is_rk
        # ========== RK3588 MPP 官方环境变量（加固硬件稳定性） ==========
        if self.is_rk:
            os.environ["MPP_PLATFORM"] = "rk3588"
            os.environ["MPP_DISABLE_REGULATOR"] = "1"
            os.environ["MPP_NO_RESET"] = "1"
            os.environ["FFMPEG_FORCE_HW"] = "1"
            # 强制单客户端独占 MPP，禁止多实例抢占
            os.environ["MPP_SINGLE_INSTANCE"] = "1"
            # 关闭 MPP 自动重连，减少驱动报错
            os.environ["MPP_RECONNECT_DISABLE"] = "1"
        self.is_read_to_image=is_read_to_image
        if is_ping is True:
            not_ip_count=0
            while True:
                ip_state=is_ip_reachable(ip)
                if ip_state is True:
                    break
                not_ip_count+=1
                if not_ip_count>self.where_ping_count:
                    raise Exception('ip:{} 地址不通'.format(ip))
                time.sleep(0.1)

        self.is_wait_state=is_wait_state #启用每张图片的，等待时间状态
        self.is_wait_time_by_fps=is_wait_time_by_fps #每张图片的，等待时间自动根据fps来计算
        if where_set_wait_time>0:#转换单位，毫秒，转秒
            where_set_wait_time=where_set_wait_time/1000
        self.where_set_wait_time=where_set_wait_time#设置的每张图片的，等待时间 毫秒

        #使用opencv 获取第一次视频的信息
        cap = cv2.VideoCapture(self.camera_rtsp, cv2.CAP_FFMPEG)
        if cap.isOpened() is False:
            print('打开视频流失败：',self.camera_rtsp)
            raise Exception('打开视频流失败：',self.camera_rtsp)
        self.get_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.get_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.get_max_size=max(self.get_w,self.get_h)
        self.fps = int(max(cap.get(cv2.CAP_PROP_FPS) % 100, 0) or 30.0)  # 20 FPS fallback
        cap.release()

        if self.is_max_size_limit and self.get_max_size>where_max_size:#等比缩小宽度
            multiple=self.get_max_size/where_max_size
            if self.get_w>=self.get_h:
                #宽度大于等于高度
                new_w = where_max_size
                new_h = int(self.get_h / multiple)
            else:
                #高度小于宽度
                new_h=where_max_size
                new_w = int(self.get_w / multiple)
            self.get_w=new_w
            self.get_h=new_h
        else:
            self.is_max_size_limit=False

        self.where_auto_wait_time = 1 / self.fps
        self.args = {
            "rtsp_transport": "tcp",
            "fflags": "+genpts+flush_packets",#discardcorrupt+nobuffer+genpts+flush_packets  +genpts+flush_packets
            "flags": "low_delay",
            "buffer_size":'100KB',#+'k' str(0) str(1024*10)+'KB'
            "async":'0',
            'max_delay':0.1,
            'skip_frame':'default',

            #"vsync":"vfr",#cfr=固定帧率 vfr=可变帧率
            # "bufsize ":str(0),#+'k'
            # 'maxrate':1024*2,
            # "stimeout":'101000000',
        }

        if output_fps is None or output_fps<=0:
            output_fps=self.fps
            self.play_fps=output_fps
        else:
            if output_fps>self.fps:
                output_fps=self.fps#帧率不能大于，最大帧率
            self.where_auto_wait_time = 1 / output_fps
            self.play_fps = self.fps
            if self.play_fps>output_fps:
                self.play_fps = output_fps

        if self.is_wait_state is True:#等待时间
            if self.is_wait_time_by_fps is True:#自动计算
                self.where_wait_time=self.where_auto_wait_time
            else:
                #手动设置
                self.where_wait_time = self.where_set_wait_time
                if self.where_wait_time<=0 and self.where_auto_wait_time>0:
                    self.where_wait_time=self.where_auto_wait_time
            if self.where_wait_time<=0:
                self.is_wait_state =False

        pix_fmt='bgr24'
        if b_rgb:
            pix_fmt = 'rgb24'
        pix_fmt=pix_fmt
        if self.is_rk:
            if self.ffmpeg_vcodec and self.ffmpeg_vcodec != "":
                self.args["c:v"] = self.ffmpeg_vcodec  # 关键：指定 RK MPP HEVC 硬解码器
            # 新增：强制硬件解码输出 NV12（RK 标准硬件帧格式，修复驱动未就绪告警）
            self.args["hwaccel_output_format"] = "nv12"

        if self.ffmpeg_hwaccel is not None and self.ffmpeg_hwaccel!='':
            self.args["hwaccel"] = self.ffmpeg_hwaccel#"cuda"  # vaapi  cuda  opencl qsv
        '''
        ffmpeg -hwaccels
            
        #NVIDIA 显卡 = cuda
        #Intel 集显=  d3d11va 、 dxva2
        #AMD 集显 =  dxva2
        #适用硬件(NVIDIA、AMD 、Intel ) = vulkan
        #微软 DirectX = d3d12va、d3d11va、dxva2
        
        vaapi
        qsv
        opencl
        
        win=
        cuda
        vaapi
        dxva2
        qsv
        d3d11va
        opencl
        vulkan
        d3d12va
        
        ubuntu=
        vdpau
        cuda
        vaapi
        qsv
        drm
        opencl

        '''
        scale_name='scale'
        # if self.is_rk:
        #     scale_name = 'scale_rkrga'
        #     pix_fmt = 'rga'
        self.process =None
        self.process = (
            ffmpeg
            .input(self.camera_rtsp, **self.args, loglevel=loglevel_input)#info warning
            .filter(scale_name, self.get_w, self.get_h)  # 添加 scale 过滤器
            .output('pipe:', format='rawvideo', pix_fmt=pix_fmt, loglevel=output_loglevel,r=output_fps,an=None)
            .run_async(pipe_stdout=True)
        )
        self.start_time = time.time()
        self.load_camera_state = True
        self.img_size=self.get_w * self.get_h * 3
        print(f" 加载摄像头：{self.camera_rtsp} 成功 框架 {self.get_w}x{self.get_h} at {output_fps:.2f} FPS)")

        self.thread_cap = Thread(target=self.update,  daemon=True)
        self.thread_cap.start()



    def update(self):
        # 读取守护进程线程中的流'i'帧
        list_time=[]
        try:
            # test_time=0
            while self.b_release is False and self.b_release_count <= 0 and self.process is not None and self.process.stdout.closed is False:

                # 读取每一帧数据
                t1=time.time()
                in_bytes = self.process.stdout.read(self.img_size)

                if self.where_discard_count>0 and self.discard_count<self.where_discard_count:
                    #丢弃前面的图片
                    self.discard_count+=1
                    time.sleep(0.01)#self.time_fps/2
                    continue
                if not in_bytes:
                    self.error_count += 1
                    # print('num=', self.num, '丢失视频数据=',self.error_count)
                    if self.error_count > self.where_out_count:
                        print('自动断开')
                        break
                    time.sleep(0.02)  # 减少等待时间
                    continue

                if self.error_count>0:
                    self.error_count = 0
                # if test_time<=0:
                #     test_time=time.time()
                #     print('测试开始=',get_str_time_by_file(test_time))
                now_time=time.time()
                self.get_float_img_time=now_time
                self.get_str_img_time = str(now_time)
                self.read_count += 1

                # t2 = time.time()
                # a1=t2-t1
                # if a1<=0:
                #     a1=0.0001
                # list_time.append(a1)
                #
                # fps=1/a1
                # avg_time=0
                # avg_fps=0
                # if len(list_time)>1:
                #     avg_time=sum(list_time)/len(list_time)
                #     avg_fps=1/avg_time
                # print('Load_camera_stream_to_ffmpeg num=',self.num,'当前耗时=',round(a1,5),'秒','当前fps=',round(fps,5),'平均耗时=',round(avg_time,5),'秒','平均fps=',round(avg_fps,5))

                frame_data_type=FrameDataType.bytes
                frame_data_data=None

                # 将字节数据转换为 NumPy 数组
                if self.is_read_to_image is True:
                    frame_data_type = FrameDataType.image
                    frame_data_data = np.frombuffer(in_bytes, np.uint8).reshape([self.get_h, self.get_w, 3])#.copy()
                else:
                    frame_data_type = FrameDataType.bytes
                    frame_data_data=in_bytes

                img_color_type=ImgColorType.BGR
                if self.b_rgb:#rgb 格式
                    img_color_type=ImgColorType.RGB

                frame_data = FrameData(self.get_float_img_time,frame_data_type , frame_data_data, self.frame_count,img_h=self.get_h,img_w=self.get_w,str_time=get_str_time(self.get_float_img_time),img_color_type=img_color_type)
                self.my_frame_queue.put(frame_data)

                if self.b_release is True:
                    break

                # save_file='temp_path/other/test_img-{}-{}.jpg'.format(get_str_time_by_file(now_time),self.read_count)
                # print(save_file)
                # cv2.imwrite(save_file,self.img)

                if self.is_wait_state is True and self.where_wait_time>0:
                    time_consuming = time.time() - t1
                    if time_consuming<self.where_wait_time:
                        where_wait_time=self.where_wait_time-time_consuming
                        # print('where_wait_time=',where_wait_time)
                        time.sleep(where_wait_time)  # 等待时间

                # if now_time-test_time>=5.0:
                #     print('测试结束=',get_str_time_by_file(now_time))
                #     break

                if self.b_release is True:
                    break
            print('update while 结束')
        except Exception as ex:
            traceback.print_exc()
            print('update 异常：')
            print(ex)
        finally:
            print('update release_cap')
            self.release_cap()

    # 释放资源
    def release_cap(self):
        if self.b_release is True:
            return
        self.b_release = True
        self.b_release_count += 1
        time.sleep(0.1)

        if self.my_frame_queue.count>0:
            self.my_frame_queue.clear()
        print('release_cap 释放资源 =',self.camera_rtsp)
        if self.process is not None:
            pid = self.process.pid
            threading.Thread(target=self.release_main_thread).start()
            time.sleep(0.5)
            threading.Thread(target=self.release_son_thread,args=[pid]).start()


    def release_main_thread(self):
        try:
            if self.process is None:
                return
            # 释放资源
            print('release_cap 释放资源 1')
            self.process.stdout.close()
            print('release_cap 释放资源 2')
            # self.process.terminate()  # 提前终止子进程
            # print('release_cap 释放资源 3')
            # self.process.wait(timeout=2)  # 方法：用于等待子进程正常结束。
            # self.process.kill()  # 方法：发送 SIGKILL 信号，强制终止子进程。
            # print('release_cap 释放资源 4')
        except Exception as ex:
            print('杀死process异常=', ex, traceback.format_exc())
            traceback.print_exc()

    def release_son_thread(self,pid):
        try:
            # 提前终止子进程
            self.process.terminate()
            try:
                # 等待子进程结束
                returncode = self.process.wait(timeout=2)
                print(f"子进程已终止，返回码: {returncode}", self.camera_rtsp, )
            except Exception as ex:
                traceback.print_exc()
                print('杀死process异常=', ex, traceback.format_exc())
                # 如果子进程没有响应 SIGTERM 信号，使用 kill() 方法强制终止
                self.process.kill()
                returncode = self.process.wait()
                print(f"子进程已被强制终止，返回码: {returncode}", self.camera_rtsp)
                kill_process(pid, is_exist=True)
        except Exception as ex:
            print('杀死process异常=', ex, traceback.format_exc())
            traceback.print_exc()
        finally:
            self.process = None
