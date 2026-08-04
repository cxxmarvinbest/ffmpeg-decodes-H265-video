import base64
import json
import math
import re
import shutil
import signal

import sys
import threading
import warnings

from typing import List
import platform

import PySide6

from PySide6 import QtGui
from PySide6.QtGui import QImage

from PySide6.QtWidgets import QFileDialog, QWidget, QMessageBox

if platform.system()=='Windows':
    import pygetwindow
    from ctypes import windll
    import win32api
    import win32con
    import win32gui
    import win32ui

    import mss
    import mss.tools
    from pygetwindow import Win32Window
    from win32api import GetMonitorInfo
    from win32api import MonitorFromPoint

from datetime import datetime
import hashlib
import os

import subprocess
import time
import traceback
import uuid
import cv2
import numpy as np
import psutil
import socket
from contextlib import closing

import yaml
from PIL import ImageGrab




def cv_imread_CN(image_path,isBGR=False):
    # file_path_gbk = image_path.encode('utf-8')
    # img_mat = cv2.imread(file_path_gbk)
    if os.path.exists(image_path) is False:
        im_file3 = os.path.basename(image_path)
        splitext1, splitext2 = os.path.splitext(im_file3)
        im_file3 = os.path.join(os.path.dirname(image_path), splitext1 + splitext2.upper())
        if os.path.exists(im_file3):
            image_path = im_file3
    if os.path.exists(image_path) is False:
        return None
    # 文件路径file_path，返回读取后的图片
    fromfile_val = np.fromfile(image_path, dtype=np.uint8)
    if fromfile_val is None:
        return fromfile_val
    cv_img = cv2.imdecode(fromfile_val, -1)
    if cv_img is not None and isBGR is True and cv_img.shape[2] == 4:
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2BGR)
    return cv_img

#判断字符串是否存在中文汉字
def contains_chinese(text):
    pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(pattern.search(text))

def cv_imwrite_CN(save_path, img):
    if img is None:
        return
    if save_path is None:
        return
    if isinstance(img, str):
        save_path2 = img
        img = save_path
        save_path = save_path2
    str_dirname = os.path.dirname(save_path)
    if str_dirname != '' and str_dirname != '/' and str_dirname != '\\' and os.path.exists(str_dirname) is False:
        os.makedirs(str_dirname, exist_ok=True)

    if contains_chinese(save_path) is True:#存在中文汉字
        imencode_data=None
        if save_path.endswith('.png'):
            imencode_data=cv2.imencode('.png', img)[1]
        else:
            imencode_data=cv2.imencode('.jpg', img)[1]
        if imencode_data is None:
            return
        try:
            imencode_data.tofile(save_path)
        except Exception as ex:
            print('保存图片失败：',ex)
            traceback.print_exc()
            cv2.imwrite(save_path, img)
    else:
        # file_path_gbk = save_path.decode('utf-8')
        cv2.imwrite(save_path, img)



def get_yamls(path):
    with open(path, encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)  # dict



# 获取UUID
def get_uuid():
    return str(uuid.uuid1())


def kill_pid(pid):
    try:
        all_pid = psutil.pids()
        if pid not in all_pid:
            return False
        process = psutil.Process(pid)
        if process is None:
            return False
        process_name = process.name()
        print('进程={} 已存在, 1s后自动关闭进程'.format(process_name))
        time.sleep(1)
        # str_system = platform.system()
        kill_process(pid)
        # if str_system=='Windows':
        #     # print('taskkill /f /im %s' % process_name)
        #     # os.system('taskkill /f /im %s' % process_name)
        #     # taskkill /f /pid
        #     print('taskkill /f /pid %s' % pid)
        #     os.system('taskkill /f /pid %s' % pid)
        # elif str_system=='Linux':
        #     print('taskkill /f /pid %s' % pid)
        #     os.system('taskkill /f /pid %s' % pid)
        return True
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    return False
#杀死进程
def kill_process(pid,is_exist=False,count=5):
    try:
        if is_exist is True:
            all_pid = psutil.pids()
            if pid not in all_pid:
                return False#不存在
        os.kill(pid, signal.SIGTERM)
        print(f"已向进程 {pid} 发送 SIGTERM 信号。")

        # 等待一段时间，给进程一些时间进行清理
        for i in range(count):
            try:
                # 尝试获取进程状态，如果进程已经退出，os.kill(pid, 0) 会抛出 ProcessLookupError
                os.kill(pid, 0)
                time.sleep(1)
            except ProcessLookupError:
                print(f"进程 {pid} 已正常退出。")
                return

        # 如果等待一段时间后进程仍未退出，发送 SIGKILL 信号强制终止
        os.kill(pid, signal.SIGKILL)
        print(f"进程 {pid} 未在规定时间内退出，已发送 SIGKILL 信号强制终止。")

    except ProcessLookupError:
        print(f"错误：进程 {pid} 不存在。")
    except PermissionError:
        print(f"错误：没有权限杀死进程 {pid}。")
    except Exception as e:
        print(f"发生未知错误：{e}")


def get_port_run(port):
    ret = 0 #256
    str_system = platform.system()
    str_code = ''
    if str_system == 'Windows':
        try:
            # 要执行的CMD命令
            command = 'netstat -aon|findstr "' + str(port) + '"'
            # 执行CMD命令
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 获取执行结果
            out, err = p.communicate()
            if out is None:
                ret = 0
                return ret
            str_out = out.decode('gbk')
            if str_out is None or str_out == '':
                ret = 0
                return ret
            if 'TIME_WAIT' in str_out and 'TCP' in str_out:
                ret = 0
                return ret
            str_out = str_out.strip().rstrip()
            if str_out == '':
                ret = 0
                return ret
            arr_out = str_out.split('\r\n')
            if len(arr_out) <= 0:
                ret = 0
                return ret
            list_data = []
            for item in arr_out:
                arr_item = item.split(' ')
                arr_item2 = []
                for item2 in arr_item:
                    if item2 is None or item2 == '':
                        continue
                    arr_item2.append(item2)
                if len(arr_item2) != 5:
                    continue
                dic_item = dict()
                dic_item[arr_item2[0] + '1'] = arr_item2[1]
                dic_item[arr_item2[0] + '2'] = arr_item2[2]
                dic_item[arr_item2[3]] = arr_item2[4]
                list_data.append(dic_item)
            if len(list_data) > 0:
                ret = len(list_data)

        except Exception as ex:
            ret = -1
            print(ex)
            traceback.print_exc()

    elif str_system == 'Linux':
        pids=get_pid_by_port(port)
        if len(pids)>0:
            ret = 1
        # command = ''
        # command += 'port=`netstat -nlt|grep ' + str(port) + '|wc -l` \n'
        # command += 'if [ $port -ne 1 ] \n'
        # command += 'then \n'
        # command += ' echo 0 \n'
        # command += 'else \n'
        # command += ' echo 1 \n'
        # command += 'fi \n'
        # try:
        #     # 执行CMD命令
        #     p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #     # 获取执行结果
        #     out, err = p.communicate()
        #     str_out = str(out)
        #     if str_out == "b'1\\n'":
        #         ret = 1  # run
        #     else:
        #         ret = 0  # end
        #     # str_err = str(err)
        #     # print('str_out=' + str_out)
        #     # print('str_err=' + str_err)
        # except Exception as ex:
        #     ret = -1
        #     print(ex)
        #     traceback.print_exc()

        # str_code = 'lsof -i:' + str(port)
        # if is_sudo is True:
        #     str_code = 'sudo ' + str_code
        # try:
        #     ret = os.system(str_code)
        # except Exception as ex:
        #     ret = -1
        #     print(ex)
        #     traceback.print_exc()
    return ret


def end_taskkill(pid):
    try:
        # 要执行的CMD命令
        command = 'taskkill /f  /pid ' + str(pid) + ' /t'
        # 执行CMD命令
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 获取执行结果
        out, err = p.communicate()
        if err is not None:
            if platform.system() == 'Windows':
                str_err = err.decode('gbk')
                print('gbk->', str_err)
            else:
                str_err = err.decode('utf-8')
                print('utf-8->', str_err)
    except Exception as ex:
        print(ex)
        traceback.print_exc()

def get_pid_by_port(port):
    try:
        # 使用 lsof 命令查找监听指定端口的进程
        command = f"lsof -t -i:{port}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        if output:
            pids = output.split('\n')
            return [int(pid) for pid in pids]
        else:
            return []
    except Exception as e:
        print(f"发生错误: {e}")
        return []


def end_port_pid(port):
    ret = 256
    str_system = platform.system()
    if str_system == 'Windows':
        try:

            # 要执行的CMD命令
            command = 'netstat -aon|findstr "' + str(port) + '"'
            # 执行CMD命令
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 获取执行结果
            out, err = p.communicate()
            if out is None:
                ret = 0
                return ret
            str_out = out.decode('gbk')
            if str_out is None or str_out == '':
                ret = 0
                return ret
            str_out = str_out.strip().rstrip()
            if str_out == '':
                ret = 0
                return ret
            arr_out = str_out.split('\r\n')
            if len(arr_out) <= 0:
                ret = 0
                return ret
            list_data = []
            for item in arr_out:
                arr_item = item.split(' ')
                arr_item2 = []
                for item2 in arr_item:
                    if item2 is None or item2 == '':
                        continue
                    arr_item2.append(item2)
                if len(arr_item2) != 5:
                    continue
                dic_item = dict()
                dic_item[arr_item2[0] + '1'] = arr_item2[1]
                dic_item[arr_item2[0] + '2'] = arr_item2[2]
                dic_item[arr_item2[3]] = arr_item2[4]
                list_data.append(dic_item)
            if len(list_data) > 0:
                for item in list_data:
                    if 'LISTENING' in item:
                        pid = item['LISTENING']
                        end_taskkill(pid)
                    if 'ESTABLISHED' in item:
                        pid = item['ESTABLISHED']
                        end_taskkill(pid)

        except Exception as ex:
            ret = -1
            print(ex)
            traceback.print_exc()
    elif str_system == 'Linux':
        pids = get_pid_by_port(port)
        if len(pids)>0:
            for item in pids:
                kill_pid(item)
        # str_code = "pid=$(sudo lsof -i:" + str(port) + " |grep LISTEN| awk '{print $2}')\n"
        # str_code += 'echo "pid=$pid"\n'
        # str_code += 'b=0\n'
        # str_code += 'if ! [ "x$pid" = "x" ]; then\n'
        # str_code += '  if [ "$pid" -gt "$b" ]; then\n'
        # str_code += '      echo "端口上的终止进程 ' + str(port) + ' ,关闭 服务 ..."\n'
        # str_code += '      echo $pid\n'
        # str_code += '      sudo kill -9 $pid\n'
        # str_code += '  fi\n'
        # str_code += 'fi\n'
        # if is_sudo is True:
        #     str_code = 'sudo ' + str_code
        # try:
        #     ret = os.system(str_code)
        # except Exception as ex:
        #     ret = -1
        #     print(ex)
        #     traceback.print_exc()
    return ret


# 获取md5
def getMd5(text):
    b = text.encode(encoding='utf-8')
    m = hashlib.md5()  # 去创建md5对象
    m.update(b)  # 生成加密字符串
    sign = m.hexdigest()  # 获取加密后的字符串
    return sign.upper()


# 获取 uuid
def get_uuid():
    return str(uuid.uuid1())


# 获取base64
def get_base64_data(image_cv, max_w=80, max_h=150, is_size=False):
    img_w = image_cv.shape[1]
    img_h = image_cv.shape[0]
    if is_size is True and (img_w > max_w or img_h > max_h):
        new_w = 0
        new_h = 0
        if img_w > max_w and img_h > max_h:
            # 等比缩放
            for i in range(999, 1, -1):
                ss = ((float(i)) / 10.0) / 100.0
                new_w = int(ss * float(img_w))
                new_h = int(ss * float(img_h))
                if new_w <= max_w and new_h <= max_h:
                    break
        elif img_w > max_w:
            # 缩放高度，固定宽度
            p = img_w / img_h
            new_w = max_w
            new_h = int(new_w / p)
        elif img_h > max_h:
            # 缩放宽度，固定高度
            p = img_w / img_h
            new_h = max_h
            new_w = int(new_h * p)

        image_back = image_cv.copy()
        image_back = cv2.resize(image_back, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        image_back = image_cv
    image = cv2.imencode('.jpg', image_back)[1]
    ss = base64.b64encode(image)
    base64_data = str(ss)[2:-1]
    return base64_data

# 获取文件的文本信息
def get_file_text(path):
    text = ''
    if os.path.exists(path) is False:
        return text
    try:
        with open(path, "r", encoding='utf-8') as f:
            text = f.read()
    except Exception as ex:
        print('读取文件异常：')
        print(ex)
    return text


# 获取时间格式化 yyyy-mm-dd hh:mm:ss.fff
def get_str_time(t=None):
    if t is not None:
        now_time = datetime.fromtimestamp(t)
    else:
        now_time = datetime.now()
    return now_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


# 获取时间格式化 yyyy-mm-dd hh:mm:ss.fff
def get_str_time_by_file(t=None,fmt="%Y-%m-%d %H-%M-%S.%f"):
    if t is not None:
        now_time = datetime.fromtimestamp(t)
    else:
        now_time = datetime.now()
    if '.%f' not in fmt:
        return now_time.strftime(fmt)
    return now_time.strftime(fmt)[:-3]

# 截图图片
def get_ori_img_by_box_xywh(src_img, box_xywh):
    x1, y1, x2, y2 = box_xywh[0], box_xywh[1], box_xywh[0] + box_xywh[2], box_xywh[1] + box_xywh[3]
    new_img = src_img[int(y1):int(y2), int(x1):int(x2)]
    return new_img

# 截图图片
def get_ori_img_by_box_xyxy(src_img, box_xyxy):
    x1, y1, x2, y2 = box_xyxy
    new_img = src_img[int(y1):int(y2), int(x1):int(x2)]
    return new_img

# base64字符串转图片
def base64_to_image_cv(base64Data):
    state, msg, image_cv = False, '', None
    try:
        if ' ' in base64Data:
            base64Data = base64Data.replace(' ', '+')
        imagedata = base64.b64decode(base64Data)
        nparr = np.frombuffer(imagedata, np.uint8)
        if nparr is None:
            msg = 'base64转流失败'
            return state, msg, image_cv
        image_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image_cv is None:
            msg = 'base64转流失败'
            return state, msg, image_cv
        state = True
    except Exception as ex:
        msg = str(ex)
    return state, msg, image_cv


def set_file_text(path, text):
    with open(path, "w", encoding='utf-8') as f:
        f.write(text)


# 自动创建文件的目录
def auto_create_dir_path(file_path):
    if file_path is None or file_path == '':
        return False
    str_dirname = os.path.dirname(file_path)
    if os.path.exists(str_dirname) is True:
        return False
    # 创建文件夹
    try:
        os.makedirs(str_dirname, exist_ok=True)
    except Exception as ex:
        traceback.print_exc()
        print('创建文件夹[' + str_dirname + ']失败：', ex)


#清空一个QWidget的所有子控件
def clear_widget_children(widget:QWidget):
    """
    清空一个QWidget的所有子控件。
    :param widget: QWidget对象
    """
    if widget is None:
        return
    for item in widget.children():
        if isinstance(item, QWidget):  # 确保只移除QWidget类型的子控件
            item.setParent(None)  # 将子控件的父控件设置为None，从而移除它

lock_get_window_capture = threading.Lock()#截图锁
lock_get_window_capture_by_hwnd = threading.Lock()#截图锁


# 通过窗口句柄截取当前句柄图片 返回cv2格式的Mat数据 笔记本电脑不行
def get_window_capture(hwnd,is_to_BGR=False, picture_name=None,x1=None, y1=None, x2=None, y2=None,is_get_rect=False):
    with lock_get_window_capture:
        return get_window_capture2(hwnd,is_to_BGR=is_to_BGR, picture_name=picture_name,x1=x1, y1=y1, x2=x2, y2=y2,is_get_rect=is_get_rect)

def get_window_capture2(hwnd,is_to_BGR=False, picture_name=None,x1=None, y1=None, x2=None, y2=None,is_get_rect=False):
    if win32gui.IsWindow(hwnd)==0:
        print(hwnd,'句柄不存在')
        if is_get_rect is True:
            return None,None
        return None#句柄不存在
    if x1 is None or y1 is None or x2 is None or y2 is None:
        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小
    width = int(x2 - x1)
    height = int(y2 - y1)
    if width<=50 or height<=50:
        #太小了
        if is_get_rect is True:
            return None,None
        return None
    img = None
    try:
        win32gui.SetActiveWindow(hwnd)
        hwndDC = win32gui.GetWindowDC(hwnd)  # 通过应用窗口句柄获得窗口DC
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)  # 通过hwndDC获得mfcDC(注意主窗口用的是win32gui库，操作位图截图是用win32ui库)
        neicunDC = mfcDC.CreateCompatibleDC()  # 创建兼容DC，实际在内存开辟空间（ 将位图BitBlt至屏幕缓冲区（内存），而不是将屏幕缓冲区替换成自己的位图。同时解决绘图闪烁等问题）
        savebitmap = win32ui.CreateBitmap()  # 创建位图
        width = int(x2 - x1)
        height = int(y2 - y1)

        savebitmap.CreateCompatibleBitmap(mfcDC, width, height)  # 设置位图的大小以及内容
        neicunDC.SelectObject(savebitmap)  # 将位图放置在兼容DC，即 将位图数据放置在刚开辟的内存里

        neicunDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)  # 截取位图部分，并将截图保存在剪贴板
        if picture_name is not None:
            savebitmap.SaveBitmapFile(neicunDC, picture_name)  # 将截图数据从剪贴板中取出，并保存为bmp图片

        img_buf = savebitmap.GetBitmapBits(True)

        img = np.frombuffer(img_buf, dtype="uint8")
        img.shape = (height, width, 4)
        if is_to_BGR is True:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # 释放内存
        win32gui.DeleteObject(savebitmap.GetHandle())
        neicunDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
    except Exception as e:
        print('取图异常：',e)
        # traceback.print_exc()
    if is_get_rect is True:
        return img,(x1, y1,width,height)
    return img

# 通过窗口句柄截取当前句柄图片 返回cv2格式的Mat数据 完美解决
def get_window_capture_by_hwnd(hwnd,is_to_BGR=False, x1=None, y1=None, x2=None, y2=None,is_get_rect=False,hwnd_dc=None,mfc_dc=None,save_dc=None):
    with lock_get_window_capture_by_hwnd:
        return get_window_capture_by_hwnd2(hwnd,is_to_BGR=is_to_BGR, x1=x1, y1=y1, x2=x2, y2=y2,is_get_rect=is_get_rect,hwnd_dc=hwnd_dc,mfc_dc=mfc_dc,save_dc=save_dc)


def get_window_capture_by_hwnd2(hwnd,is_to_BGR=False, x1=None, y1=None, x2=None, y2=None,is_get_rect=False,hwnd_dc=None,mfc_dc=None,save_dc=None):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        if is_get_rect is True:
            return None, None
        return None  # 句柄不存在
    if x1 is None or y1 is None or x2 is None or y2 is None:
        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小
    width = int(x2 - x1)
    height = int(y2 - y1)
    if width <= 50 or height <= 50:
        # 太小了
        if is_get_rect is True:
            return None, None
        return None
    img = None
    # Adapted from https://stackoverflow.com/questions/19695214/screenshot-of-inactive-window-printwindow-win32gui
    try:
        # windll.user32.SetProcessDPIAware()

        b_hwnd_dc = False
        if hwnd_dc is None:
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            b_hwnd_dc = True
        b_mfc_dc = False
        if mfc_dc is None:
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            b_mfc_dc = True
        b_save_dc = False
        if save_dc is None:
            save_dc = mfc_dc.CreateCompatibleDC()
            b_save_dc = True
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        # If Special K is running, this number is 3. If not, 1
        result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)  # 1
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4))
        img = np.ascontiguousarray(img)[..., :-1]  # make image C_CONTIGUOUS and drop alpha channel
        if is_to_BGR is True and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        # if not result:  # result should be 1
        #     win32gui.DeleteObject(bitmap.GetHandle())
        #     save_dc.DeleteDC()
        #     mfc_dc.DeleteDC()
        #     win32gui.ReleaseDC(hwnd, hwnd_dc)
        #     raise RuntimeError(f"Unable to acquire screenshot! Result: {result}")

        # # 释放内存
        win32gui.DeleteObject(bitmap.GetHandle())
        if b_save_dc:
            save_dc.DeleteDC()
        if b_mfc_dc:
            mfc_dc.DeleteDC()
        if b_hwnd_dc:
            win32gui.ReleaseDC(hwnd, hwnd_dc)

    except Exception as e:
        print('取图异常：', e)
        # traceback.print_exc()
    if is_get_rect is True:
        return img, (x1, y1, width, height)
    return img

# 居中缩放图片
def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
    # Resize and pad image while meeting stride-multiple constraints
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return im, ratio, (dw, dh)


def set_qt_lable_img(image, lable, img_type='qt',is_img_RGB=False):
    try:
        lable_width = lable.width()
        lable_height = lable.height()
        if img_type != 'qt':
            image = cvimg_to_qtimg(image, lable_width, lable_height,is_img_RGB=is_img_RGB)
            if image is None:
                return
            image = QtGui.QPixmap.fromImage(image)

        img_h = image.height()
        img_w = image.width()
        if img_w != lable_width or img_h != lable_height:
            # 缩放图片
            image = image.scaled(lable_width, lable_height)
        lable.setPixmap(image)

    except Exception as ex:
        traceback.print_exc()
        print('异常：'+str(ex))


def set_qt_lable_img_return_proportion(image, lable, img_type='qt'):
    lable_width = lable.width()
    lable_height = lable.height()
    ratio, dw_dh = None, None
    if img_type != 'qt':
        image,ratio, dw_dh = cvimg_to_qtimg_return_proportion(image, lable_width, lable_height)
        image = QtGui.QPixmap.fromImage(image)
    img_h = image.height()
    img_w = image.width()
    if img_w != lable_width or img_h != lable_height:
        # 缩放图片
        image = image.scaled(lable_width, lable_height)
    lable.setPixmap(image)
    return ratio, dw_dh


def cvimg_to_qtimg(cvimg, lable_width, lable_height,is_img_RGB=False):
    if cvimg is None:
        return None
    try:
        height, width, depth = cvimg.shape
        if width != lable_width or height != lable_height:
            # 缩放图片
            cvimg,ratio, dw_dh= letterbox(cvimg, new_shape=(lable_height, lable_width), color=(0, 0, 0),
                                                       auto=False, scaleFill=False, scaleup=True, stride=2)
            height, width, depth = cvimg.shape
        if is_img_RGB is False:
            #如果是 BGR 格式，则需要转 RGB格式
            cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
        depth=cvimg.shape[2]
        cvimg = QImage(cvimg.data, width, height, width * depth, QImage.Format.Format_RGB888)
        return cvimg
    except Exception as ex:
        traceback.print_exc()
        print(ex)
    return None

def cvimg_to_qtimg_return_proportion(cvimg, lable_width, lable_height):
    height, width, depth = cvimg.shape
    ratio, dw_dh=None,None
    if width != lable_width or height != lable_height:
        # 缩放图片
        cvimg,ratio, dw_dh= letterbox(cvimg, new_shape=(lable_height, lable_width), color=(0, 0, 0),
                                                   auto=False, scaleFill=False, scaleup=True, stride=2)
        height, width, depth = cvimg.shape
    else:
        ratio=(1,1)
        dw_dh=(0,0)
    cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    cvimg = QImage(cvimg.data, width, height, width * depth, QImage.Format.Format_RGB888)
    return cvimg,ratio, dw_dh


#获取窗口位置信息
def get_window_rect_xyxy(hwnd):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        return None  # 句柄不存在
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    return x1, y1, x2, y2

#获取窗口位置信息
def get_window_rect_xywh(hwnd):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        return None  # 句柄不存在
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    return x1, y1, int(x2-x1), int(y2-y1)

#获取QT QPixmap
def get_QPixmap_by_hwnd_and_screen(hwnd,screen,is_get_rect=False):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        if is_get_rect is True:
            return None,None
        return None  # 句柄不存在
    data=None

    if is_get_rect is True:
        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
        data= screen.grabWindow(hwnd),(x1, y1, x2-x1, y2-y1)
    else:
        data = screen.grabWindow(hwnd)
    return data

#获取QT QImage
def get_QImage_by_hwnd_and_screen(hwnd,screen,is_get_rect=False):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        if is_get_rect is True:
            return None,None
        return None  # 句柄不存在
    data = None
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    width = int(x2 - x1)
    height = int(y2 - y1)
    if width<=50 or height<=50:
        #太小了
        if is_get_rect is True:
            return None,None
        return None
    if is_get_rect is True:
        data = screen.grabWindow(hwnd).toImage(), (x1, y1, x2 - x1, y2 - y1)
    else:
        data = screen.grabWindow(hwnd).toImage()
    return data

#QImage 转 Opencv图像
def qimage_to_cvimage(qimage):
    buf = qimage.constBits()  # 获取图像数据的指针
    width, height = qimage.width(), qimage.height()  # 获取图像的宽度和高度
    buf.setsize(qimage.byteCount())  # 设置缓冲区的大小为图像的字节数
    return np.array(buf).reshape(height, width, 4).copy()  # 将缓冲区转换为 NumPy 数组，并重新形状为图像尺寸

#获取QT QImage Opencv
def get_QImage_cv_by_hwnd_and_screen(hwnd,screen,is_get_rect=False,is_to_BGR=False):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        if is_get_rect is True:
            return None,None
        return None  # 句柄不存在
    data = None
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    width = int(x2 - x1)
    height = int(y2 - y1)
    if width<=50 or height<=50:
        #太小了
        if is_get_rect is True:
            return None,None
        return None
    image=screen.grabWindow(hwnd).toImage()
    image=qimage_to_cvimage(image)
    if is_to_BGR is True:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if is_get_rect is True:
        data = image, (x1, y1, x2 - x1, y2 - y1)
    else:
        data = image
    return data


#获取屏幕截图
def get_window_screen_screenshot_by_hwnd_ImageGrab(hwnd,x1=None, y1=None, x2=None, y2=None,is_get_rect=False,is_to_BGR=False):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        if is_get_rect is True:
            return None,None
        return None  # 句柄不存在
    data = None
    if x1 is None or y1 is None or x2 is None or y2 is None:
        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小

    width = int(x2 - x1)
    height = int(y2 - y1)
    if width<=50 or height<=50:
        #太小了
        if is_get_rect is True:
            return None,None
        return None

    img = ImageGrab.grab(bbox=(x1, y1, x2, y2 ))  # bbox 定义左、上、右和下像素的4元组
    img = np.array(img.getdata(), np.uint8).reshape(img.size[1], img.size[0], 3)#opencv 图片
    if is_to_BGR is True:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    if is_get_rect is True:
        data = img, (x1, y1, x2 - x1, y2 - y1)
    else:
        data = img
    return data

#获取屏幕截图
def get_window_screen_screenshot_by_hwnd_mss(_mss,hwnd,x1=None, y1=None, x2=None, y2=None,is_get_rect=False,is_to_BGR=False):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        if is_get_rect is True:
            return None,None
        return None  # 句柄不存在
    data = None
    if x1 is None or y1 is None or x2 is None or y2 is None:
        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小

    width = int(x2 - x1)
    height = int(y2 - y1)
    if width<=50 or height<=50:
        #太小了
        if is_get_rect is True:
            return None,None
        return None

    monitor={'left':x1,'top':y1,'width':x2-x1,'height':y2-y1}

    screenshot=_mss.grab(monitor)
    img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
    img_array = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if is_get_rect is True:
        data = img, (x1, y1, x2 - x1, y2 - y1)
    else:
        data = img
    # cv2.imwrite('img.jpg',img)
    return data

#获取 Win32Window
def get_Win32Window(hwnd_id):
    AllWindows: List[Win32Window] = pygetwindow.getAllWindows()
    win32Window: Win32Window = None
    for item in AllWindows:
        if item._hWnd == hwnd_id:
            win32Window = item
            break

    return win32Window



def on_screen_window_boundary_auto(win32Window,rect_xywh,hwnd_id,max_width,max_height):

    # 自动处理越界问题
    if rect_xywh[0] < 0:  # 左边 越界
        win32Window.moveTo(0, rect_xywh[1])
        rect_xywh = get_window_rect_xywh(hwnd_id)
    if rect_xywh[1] < 0:  # 上边 越界
        win32Window.moveTo(rect_xywh[1], 0)
        rect_xywh = get_window_rect_xywh(hwnd_id)
    if rect_xywh[0] + rect_xywh[2] > max_width:  # 右边 越界
        win32Window.moveTo(max_width - rect_xywh[2], rect_xywh[1])
        rect_xywh = get_window_rect_xywh(hwnd_id)
    if rect_xywh[1] + rect_xywh[3] > max_height:  # 下边 越界
        win32Window.moveTo(rect_xywh[0], max_height - rect_xywh[3])
        rect_xywh = get_window_rect_xywh(hwnd_id)
    return rect_xywh

#获取任务栏尺寸（这里假设任务栏在屏幕的底部）
def get_window_taskbar_height():
    # 获取任务栏尺寸（这里假设任务栏在屏幕的底部）
    a1=win32api.GetSystemMetrics(win32con.SM_CYBORDER)
    a2=win32api.GetSystemMetrics(win32con.SM_CYSIZE)
    a3=win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
    taskbar_height1 =  a1+ a2 + a3

    monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
    monitor = monitor_info.get('Monitor')  # 屏幕分辨率
    work = monitor_info.get('Work')  # 工作区间
    taskbar_height2=monitor[3] - work[3]  # 任务栏高度
    taskbar_height1= min(taskbar_height1,taskbar_height2)
    if taskbar_height1>50:
        taskbar_height1-=10
    return taskbar_height1

#获取相交的面积
def get_intersect_area(box_xywh1, box_xywh2):
    a1 = min(box_xywh1[0] + box_xywh1[2], box_xywh2[0] + box_xywh2[2])
    a2 = max(box_xywh1[0], box_xywh2[0])
    dx = a1 - a2
    b1 = min(box_xywh1[1] + box_xywh1[3], box_xywh2[1] + box_xywh2[3])
    b2 = max(box_xywh1[1], box_xywh2[1])
    dy = b1 - b2
    if dx >= 0 and dy >= 0:
        return dx * dy
    else:
        return 0

def get_intersect_area_by_xyxy(box_xyxy1, box_xyxy2):
    box_xywh1=[box_xyxy1[0],box_xyxy1[1],box_xyxy1[2]-box_xyxy1[0],box_xyxy1[3]-box_xyxy1[1]]
    box_xywh2=[box_xyxy2[0],box_xyxy2[1],box_xyxy2[2]-box_xyxy2[0],box_xyxy2[3]-box_xyxy2[1]]
    return get_intersect_area(box_xywh1, box_xywh2)

#判断是否相交
def is_rectangle_intersect(box_xywh1, box_xywh2):
    x1, y1, x2, y2 = box_xywh1[0], box_xywh1[1], box_xywh1[0] + box_xywh1[2], box_xywh1[1] + box_xywh1[3]
    x3, y3, x4, y4 = box_xywh2[0], box_xywh2[1], box_xywh2[0] + box_xywh2[2], box_xywh2[1] + box_xywh2[3]

    if x1 < x4 and x2 > x3 and y1 < y4 and y2 > y3:
        return True
    return False

#判断是否相交
def is_rectangle_intersect_by_xyxy(box_xyxy1, box_xyxy2):
    x1, y1, x2, y2 = box_xyxy1
    x3, y3, x4, y4 = box_xyxy2

    if x1 < x4 and x2 > x3 and y1 < y4 and y2 > y3:
        return True
    return False

#获取相交状态和比例
def get_intersect_and_proportion(box_xywh1, box_xywh2):
    state, proportion = False, 0
    if is_rectangle_intersect(box_xywh1,box_xywh2) is False:
        return state, proportion
    state = True
    proportion = get_intersect_area(box_xywh1,box_xywh2) / (box_xywh2[2]*box_xywh2[3])
    return state, proportion

#计算两个坐标点的距离
def get_distance_2d(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return abs(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

#计算列表坐标点的距离
def get_distance_list(list_point):
    """
    计算列表坐标点的距离
    Args:
        list_point: [(x,y)]

    Returns:

    """
    distance=0
    if len(list_point)<2:
        return distance
    for i in range(len(list_point)-1):
        item1=list_point[i]
        item2=list_point[i+1]
        distance+=get_distance_2d(item1,item2)
    return distance

#获取子控件
def get_window_handles(hwnd_id):
    handles = []
    win32gui.EnumChildWindows(hwnd_id, lambda hwnd, param: param.append(hwnd), handles)
    return handles

#发送鼠标点击
def send_click_message(x, y, hwnd, interval=0.005,tip='',task_num=-1,is_test_video=False,is_not_msg=False):
    if win32gui.IsWindow(hwnd) == 0:
        print(hwnd, '句柄不存在')
        return # 句柄不存在
    str_time=get_str_time()
    if is_not_msg is False:
        print('任务=',task_num,tip,'发送鼠标点击->',"x:",x,"y:", y, "hwnd:", hwnd,str_time)
    if is_test_video is True:
        return #测试视频不用真的发送消息
    # 使用 MAKELONG 函数将 x 和 y 坐标组合成一个长整型值
    long_position = win32api.MAKELONG(x, y)
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN,win32con.MK_LBUTTON, long_position)
    if interval>0:
        time.sleep(interval)#加一个间隔时间
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, long_position)

# 列表排序，正负分离 再重组，从大到小
def zf_sort(list_data):
    list_z, list_f = [], []
    for temp in list_data:
        if temp > 0:
            list_z.append(temp)
        else:
            list_f.append(temp)

    list_z.sort()
    list_f.sort(reverse=True)
    return list_z + list_f

#转换华为的抓拍图片
def get_SDC_snapAction_img_by_multipart_bytes(http_bytes):
    image,msg=None,''
    try:
        haed,body = http_bytes.split(b'\r\n', 1)
        json_data,form_data,_=body.split(haed, 2)
        # json_data= str_to_json(json_data.split(b'\r\n\r\n',1)[1].decode('utf-8'))
        form_data,image_bytes=form_data.split(b'\r\n\r\n',2)

        # with open('image.jpg','wb') as f:
        #     f.write(image_bytes)

        # 将 bytes 数据转换为 numpy 数组
        image_array = np.frombuffer(image_bytes, np.uint8)

        # 使用 cv2.imdecode 解码数组为 OpenCV 图像
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    except Exception as ex:
        traceback.print_exc()
        msg=str(ex)
    return image,msg

#python 字符串时间转时间戳
def string_to_timestamp(time_string, format_string="%Y-%m-%d %H:%M:%S"):
    try:

        dt = datetime.strptime(time_string, format_string)
        timestamp = dt.timestamp()
        return timestamp
    except ValueError:
        print("错误: 输入的时间字符串与格式不匹配!")
        return None

#判断ip地址是否可通，支持win系统和linux系统
def is_ip_reachable(ip:str,is_log=True):
    system = platform.system()
    try:
        if system == "Windows":
            # Windows 系统的 ping 命令参数
            ping_command = ['ping', '-n', '1', '-w', '1000', ip]
            encoding = 'gbk'  # Windows 系统默认编码
        elif system == "Linux":
            # Linux 系统的 ping 命令参数
            ping_command = ['ping', '-c', '1', '-W', '1', ip]
            encoding = 'utf-8'  # Linux 系统默认编码
        else:
            print("不支持的操作系统。")
            return False
        # 执行 ping 命令
        result = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.stdout is not None:
            str_data=result.stdout.decode(encoding=encoding)
            if is_log:
                print(str_data)
            if system == "Windows":
                if '请求超时' in str_data:
                    return False
                if '无法访问' in str_data:
                    return False
            elif system == "Linux":
                if '请求超时' in str_data:
                    return False
                if '无法访问' in str_data:
                    return False
                if 'timeout' in str_data:
                    return False
                if 'cannot' in str_data:
                    return False
                if 'Destination Host Unreachable' in str_data:
                    return False

        # 判断命令执行结果
        return result.returncode == 0
    except Exception as ex:
        print(f"发生错误: {ex}")
        traceback.print_exc()
        return False


#获取人脸编号
def get_max_personnel_number_name(num,max_len):
    str_name=str(num)
    for i in range(max_len):
        if len(str_name)>=max_len:
            break
        str_name='0'+str_name
    return str_name

#获取IP的网关地址
def get_gateway_value(ip):
    gateway_value = None
    if ip is None or ip=='':
        return gateway_value
    # 使用点号作为分隔符对 IP 地址进行分割
    parts = ip.split('.')
    if len(parts)!=4:
        return gateway_value
    # 检查分割后的列表长度是否符合 IP 地址格式
    try:
        # 获取第三段数值（索引为 2）
        gateway_value = int(parts[2])
    except Exception as ex:
        traceback.print_exc()
        print("IP 地址的第三段不是有效的整数：",ip)
    return gateway_value

#保存测试图片 异步
def on_save_test_img_thread(img_bg,all_file,is_image_rgb=False):
    #异步保存，避免阻塞
    thread=threading.Thread(target=on_save_test_img,args=[img_bg,all_file,is_image_rgb],daemon=True)
    thread.start()

#保存测试图片 异步
def on_save_test_img(img,all_file,is_image_rgb=False):
    if is_image_rgb is True:#转BGR
        img=cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
    cv_imwrite_CN(all_file, img)

#保存测试图片 异步
def on_save_test_imgs_thread(list_img,is_image_rgb=False):
    #异步保存，避免阻塞
    thread=threading.Thread(target=on_save_test_imgs,args=[list_img,is_image_rgb],daemon=True)
    thread.start()

#保存测试多张图片 异步
def on_save_test_imgs(list_img,is_image_rgb=False):
    for img,all_file in list_img:
        if is_image_rgb is True:#转BGR
            img=cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv_imwrite_CN(all_file, img)
#移除文件
def on_remove_file(file):
    if not os.path.exists(file):
        return
    try:
        os.remove(file)
    except Exception as ex:
        print('移除文件异常：',file,ex)
        traceback.print_exc()

#pid 获取详情信息
def get_process_info(pid):
    try:
        process = psutil.Process(pid)
        info = {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),  # 进程状态（运行、睡眠、停止等）
            "create_time": process.create_time(),  # 创建时间（时间戳）
            "cpu_usage": process.cpu_percent(interval=1),  # CPU 使用率（%）
            "memory_info": process.memory_info(),  # 内存信息（包含 RSS、VMS 等）
            "memory_percent": process.memory_percent(),  # 内存使用率（%）
            "num_threads": process.num_threads(),  # 线程数
            "cmdline": process.cmdline(),  # 命令行参数
            "username": process.username(),  # 启动用户
            "parent_pid": process.parent().pid if process.parent() else None,  # 父进程 PID
        }
        return info
    except psutil.NoSuchProcess:
        print(f"PID {pid} 不存在")
    except Exception as ex:
        print(f"获取进程信息时出错：{print}")
        traceback.print_exc()
    return None

#ping ip 地址
def on_test_ping_ip(ip,where_count,my_log,is_log1=True,is_log2=True):
    not_ip_count = 0
    ping_state=False
    while True:
        if is_log1 is True:
            my_log.info('开始 ping ip:{} 地址'.format(ip))
        ip_state = is_ip_reachable(ip,is_log=is_log2)
        if ip_state is True:
            ping_state = True
            break
        not_ip_count += 1
        if not_ip_count > where_count:
            ping_state=False
            if is_log1 is True:
                my_log.warning('ping ip:{} 地址不通'.format(ip))
            break
        time.sleep(0.1)
    return ping_state

#ping ip 地址 和 端口号
def on_test_ping_ip_port(ip,port,where_count,my_log,is_log1=True,is_log2=True):
    not_ip_count = 0
    ping_state=False
    while True:
        if is_log1 is True:
            my_log.info('开始 ping ip:{} 端口：{}'.format(ip,port))
        ip_state,msg = test_ip_port_connection(ip,port)
        if ip_state is True:
            ping_state = True
            break
        else:
            if is_log2 is True and msg is not None:
                print(msg)
        not_ip_count += 1
        if not_ip_count > where_count:
            ping_state=False
            if is_log1 is True:
                my_log.warning('ping ip:{} 端口：{} 连接不通'.format(ip,port))
            break
        time.sleep(0.1)
    return ping_state

def test_ip_port_connection(ip, port, timeout=1):
    """
    测试 ip地址和端口 的连接是否可用

    :param ip:  服务器的 IP 地址或主机名
    :param port:  服务器的端口号，默认为 3306
    :param timeout: 连接超时时间（秒） 默认1秒
    :return: 连接成功返回 True，失败返回 False
    """
    state,msg=False,None
    try:
        # 创建一个 TCP 套接字
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            # 设置超时时间
            sock.settimeout(timeout)
            # 尝试连接
            result = sock.connect_ex((ip, port))
            # 如果连接成功，返回码为 0
            state = result == 0
    except socket.gaierror:
        msg="错误: 无法解析 ip：{} 端口：{}".format(ip, port)
    except socket.error as e:
        msg="错误: 连接失败:{} ip：{} 端口：{}".format(e,ip, port)
    except Exception as ex:
        msg = "错误: 连接异常:{} ip：{} 端口：{}".format(ex, ip, port)
    return  state,msg

def get_all_ip_addresses():
    ip_list = []
    try:
        str_system = platform.system()
        if str_system=='Windows':
            # hostname = socket.gethostname()
            # # 获取所有的 IP 地址信息
            # addrs = socket.getaddrinfo(hostname, None)
            # for addr in addrs:
            #     # 提取 IP 地址
            #     ip = addr[4][0]
            #     if ip not in ip_list:
            #         ip_list.append(ip)

            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == 2 and addr.address not in ip_list:
                        ip_list.append(addr.address)

        elif str_system=='Linux':
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == 2 and addr.address not in ip_list:
                        ip_list.append(addr.address)
    except Exception as e:
        print(f"发生错误: {e}")
    return ip_list

# 获取 硬盘信息
def get_disk_info():
    disk_info = psutil.disk_partitions(all=False)
    list_disk = []
    sum_total_MB = 0
    sum_used_MB = 0
    sum_free_MB = 0
    sum_total_GB = 0
    sum_used_GB = 0
    sum_free_GB = 0
    for i in range(len(disk_info)):
        item = disk_info[i]
        str_path = item.device
        if platform.system() == 'Linux':
            if item.fstype != 'ext4' and item.fstype != 'fuseblk':  # and item.fstype != 'vfat'
                continue
            str_path = item.mountpoint

        item_info = psutil.disk_usage(str_path)
        percent = item_info.percent  # 使用率 %
        total_MB = np.round(item_info.total / 1024 ** 2, 2)  # 总大小 MB
        used_MB = np.round(item_info.used / 1024 ** 2, 2)  # 使用大小 MB
        free_MB = np.round(item_info.free / 1024 ** 2, 2)  # 剩余大小 MB
        total_GB = np.round(total_MB / 1024, 2)  # 总大小 GB
        used_GB = np.round(used_MB / 1024, 2)  # 使用大小 GB
        free_GB = np.round(free_MB / 1024, 2)  # 剩余大小 GB

        sum_total_MB += total_MB
        sum_used_MB += used_MB
        sum_free_MB += free_MB

        sum_total_GB += total_GB
        sum_used_GB += used_GB
        sum_free_GB += free_GB

        item_data = {'device': item.device,
                     'mount_point': item.mountpoint,
                     'fstype': item.fstype,
                     'opts': item.opts,
                     'percent': percent,
                     'total_MB': total_MB,
                     'used_MB': used_MB,
                     'free_MB': free_MB,
                     'total_GB': total_GB,
                     'used_GB': used_GB,
                     'free_GB': free_GB,
                     }
        list_disk.append(item_data)
    sum_percent = 0
    if len(list_disk) > 0:
        sum_percent = np.round((sum_used_MB / sum_total_MB) * 100, 2)  # 总使用率
    disk_data = {'count': len(list_disk),
                 'percent': sum_percent,
                 'total_MB': np.round(sum_total_MB, 2),
                 'used_MB': np.round(sum_used_MB, 2),
                 'free_MB': np.round(sum_free_MB, 2),
                 'total_GB': np.round(sum_total_GB, 2),
                 'used_GB': np.round(sum_used_GB, 2),
                 'free_GB': np.round(sum_free_GB, 2),
                 'list_disk': list_disk}
    return disk_data

def get_disk_device_info(device):
    disk_data= get_disk_info()
    for i in range(len(disk_data['list_disk'])):
        item_disk = disk_data['list_disk'][i]
        if item_disk['device']==device:
            return item_disk
    return None


# 删除非空文件夹及其所有内容
def delete_non_empty_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
        print(f"文件夹 {folder_path} 已成功删除。")
    except FileNotFoundError:
        print(f"错误：未找到文件夹 {folder_path}。")
    except PermissionError:
        print(f"错误：没有权限删除文件夹 {folder_path}。")
    except Exception as e:
        print(f"错误：删除文件夹 {folder_path} 时出现未知错误：{e}")

#设置按钮的左右边距
def set_btn_padding_lr(btn):
    style_sheet = btn.styleSheet()
    style_sheet += '''
    PushButton[hasIcon=false] {
        padding-left: 0px;
        padding-right: 0px;
    }

    PushButton[hasIcon=true] {
        padding-left: 0px;
        padding-right: 0px;
    }
        PushButton {
        padding-left: 0px;
        padding-right: 0px;
        }
    '''
    btn.setStyleSheet(style_sheet)

#设置按钮的上下边距
def set_btn_padding_tb(btn):
    style_sheet = btn.styleSheet()
    style_sheet += '''
    PushButton[hasIcon=false] {
        padding-top: 0px;
        padding-bottom: 0px;
    }

    PushButton[hasIcon=true] {
        padding-top: 0px;
        padding-bottom: 0px;
    }
        PushButton {
        padding-top: 0px;
        padding-bottom: 0px;
        }
    '''
    btn.setStyleSheet(style_sheet)

#设置按钮的上下边距
def set_btn_padding(btn):
    style_sheet = btn.styleSheet()
    style_sheet += '''
    PushButton[hasIcon=false] {
        padding-left: 0px;
        padding-right: 0px;
        padding-top: 0px;
        padding-bottom: 0px;
    }

    PushButton[hasIcon=true] {
        padding-left: 0px;
        padding-right: 0px;
        padding-top: 0px;
        padding-bottom: 0px;
    }
        PushButton {
        padding-left: 0px;
        padding-right: 0px;
        padding-top: 0px;
        padding-bottom: 0px;
        }
    '''
    btn.setStyleSheet(style_sheet)

#设置按钮的颜色
def set_btn_color(btn,color):
    btn.setStyleSheet(btn.styleSheet() + '\n PushButton {color: '+color+';}')

#设置按钮样式
def on_set_btn_style(btn,text_color='#000',background_color='white'):
    """
    设置按钮样式
    Args:
        btn: 按钮
        text_color: 字体颜色
        background_color: 背景颜色

    Returns:

    """
    # 设置按钮QSS样式
    StyleSheet="""
        /* 普通状态样式 */
        QPushButton {
            background-color: {background-color};  /* 绿色背景 */
            border: none;
            color: {color};
            padding: 0px 0px;
            text-align: center;
            text-decoration: none;
          /*   display: inline-block;*/
            font-size: 15px;
            border-radius: 5px;
            /*box-shadow: 0 4px 8px rgba(0,0,0,0.2);*/
        }

        /* 悬停状态样式 */
        QPushButton:hover {
            background-color: {background-color};  /* 深绿色背景 */
            /* transform: translateY(-2px);  /* 上移2px */ */
           /* box-shadow: 0 6px 12px rgba(0,0,0,0.3);   更大的阴影 */

        }

        /* 按下状态样式 */
        QPushButton:pressed {
            background-color: {background-color};  /* 更深绿色背景 */
            /* transform: translateY(1px);  /* 下移1px */ */
            /* box-shadow: 0 2px 4px rgba(0,0,0,0.2);   更小的阴影 */
        }
    """
    StyleSheet=StyleSheet.replace("{background-color}",background_color)
    StyleSheet = StyleSheet.replace("{color}", text_color)
    btn.setStyleSheet(StyleSheet)

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

#提示 确认
def on_tip_yes(parent,content,title='提示',yes_btn_text='确认',icon:PySide6.QtWidgets.QMessageBox.Icon=None):
    """
    提示 确认
    Args:
        parent: 窗口对象
        content: 提示内容
        title: 标题
        yes_btn_text: 按钮名称
        icon: 图标，默认是  PySide6.QtWidgets.QMessageBox.Icon.Information
    Returns: None

    """
    if icon is None:
        icon=PySide6.QtWidgets.QMessageBox.Icon.Information
    # QMessageBox.information(parent,title, content,buttons=PySide6.QtWidgets.QMessageBox.StandardButton.Yes,defaultButton=PySide6.QtWidgets.QMessageBox.StandardButton.Yes)
    # 创建消息框
    msg_box = QMessageBox(icon,title,content,PySide6.QtWidgets.QMessageBox.StandardButton.Yes,parent)
    # 自定义按钮文本
    msg_box.setButtonText(PySide6.QtWidgets.QMessageBox.StandardButton.Yes, yes_btn_text)
    msg_box.exec()
    return True

#提示 确认 警告
def on_tip_warning(parent,content,title='提示',yes_btn_text='确认'):
    on_tip_yes(parent,content,title=title,yes_btn_text=yes_btn_text,icon=PySide6.QtWidgets.QMessageBox.Icon.Warning)

#提示 询问
def on_tip_question(parent,content,title='提示',yes_btn_text='确认',no_btn_text='取消'):
    # 创建消息框
    msg_box = QMessageBox(PySide6.QtWidgets.QMessageBox.Icon.Question,title,content,PySide6.QtWidgets.QMessageBox.StandardButton.Yes|PySide6.QtWidgets.QMessageBox.StandardButton.No,parent)
    # 自定义按钮文本
    msg_box.setButtonText(PySide6.QtWidgets.QMessageBox.StandardButton.Yes, yes_btn_text)
    msg_box.setButtonText(PySide6.QtWidgets.QMessageBox.StandardButton.No, no_btn_text)
    return msg_box.exec()==QMessageBox.StandardButton.Yes


def on_select_image(parent):
    # 打开文件对话框，筛选图片文件（支持常见格式）
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        caption="选择图片文件",
        filter="Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
    )
    # "",  # 初始路径（空字符串表示当前工作目录）
    return file_path


def cv_image_to_stream(image):
    try:
        # 将图片编码为JPEG格式
        _, buffer = cv2.imencode('.jpg', image)
        # 将编码后的图片数据转换为字节流
        stream = buffer.tobytes()
        return stream
    except Exception as e:
        print(f"错误: 发生了一个未知错误: {e}")
        return None


def get_image_from_rtsp(rtsp_url, count=1):
    state,msg,img=False,'',None
    try:
        # 打开 RTSP 流
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            cap.release()
            print("无法打开 RTSP 流，请检查地址或网络连接。")
            msg='无法打开 RTSP 流，请检查地址或网络连接。'
            return state,msg,img

        # 读取一帧图像
        for i in range(count):
            ret, img = cap.read()
            if not ret:
                msg = '无法读取图像帧'
                return state, msg, img

        state=True
        # 释放资源
        cap.release()
    except Exception as ex:
        print(f"发生错误: {ex}")
        traceback.print_exc()
    return state,msg,img

# 获取 uuid
def get_create_uuid():
    str_uuid = str(uuid.uuid1()).replace('-', '')
    end_index = 9  # int(len(str_uuid) / 3)
    str_uuid = str_uuid[0:end_index]
    strTime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    microsecond = datetime.now().microsecond
    str_uuid2 = strTime + '_' + str(microsecond) + '_' + str_uuid
    return str_uuid2

# 加载配置文件
def get_yaml_values(path):
    values = None
    with open(path, encoding='utf-8') as f:
        # , Loader=yaml.FullLoader
        try:
            values = yaml.load(f, Loader=yaml.FullLoader)  # dict
        except Exception as ex:
            values = yaml.load(f)  # dict
    return values

def str_to_json(text, error_count=10):
    json_data = json.loads(text)
    if isinstance(json_data, str) is True:
        print('转换json失败，结果是str，开始补救')
        for i in range(error_count):
            json_data = json.loads(json_data)
            if isinstance(json_data, str) is False:
                print('补救　i=', i, ' 成功')
                break
        if isinstance(json_data, str) is True:
            print('补救json失败')
    return json_data

# 获取最佳的 index 口罩 类型
def get_optimum_index(img_h, img_w, count, list_xywh, where_type=2):
    # list_xywh.sort(key=lambda x: x[5])  # 按照面积排序
    # 选出中心点最顶的一个
    select_index = 0
    # where_type = 1  # 1= 面积最大 ，2= 距离中间点最近
    if where_type == 1:
        # 面积最大
        max_area = 0
        for i in range(count):
            x, y, w, h, area, c_x, c_y, face_index = list_xywh[i]
            if area > max_area:
                max_area = area
                select_index = i

    elif where_type == 2:
        # 最接近中间点的
        fabsX = 9999
        fabsY = 0
        img_w2 = img_w / 2
        for i in range(count):
            x, y, w, h, area, c_x, c_y, face_index = list_xywh[i]
            xx1 = abs(img_w2 - c_x)
            if xx1 < fabsX:
                fabsX = xx1
                fabsY = c_y
                select_index = i
            elif xx1 == fabsX and c_y > fabsY:
                fabsX = xx1
                fabsY = c_y
                select_index = i

    return select_index

# 截图头部的图片
def get_head_img(img, face_box_xywh, expand=0.5):
    img_w = img.shape[1]
    img_h = img.shape[0]
    face_box_x, face_box_y, face_box_w, face_box_h = face_box_xywh
    expand_w = int(expand * face_box_w)
    expand_h = int(expand * face_box_h)
    box_face_cropping_xywh = [face_box_x - expand_w, face_box_y - expand_h, face_box_w + expand_w * 2,
                              face_box_h + expand_h * 2]
    if box_face_cropping_xywh[0] < 0:
        box_face_cropping_xywh[0] = 0
    if box_face_cropping_xywh[1] < 0:
        box_face_cropping_xywh[1] = 0
    if box_face_cropping_xywh[2] > img_w:
        box_face_cropping_xywh[2] = img_w
    if box_face_cropping_xywh[3] > img_h:
        box_face_cropping_xywh[3] = img_h
    cropping_face_img = get_ori_img_by_box_xywh(img, box_face_cropping_xywh).copy()

    return cropping_face_img, expand_w, expand_h


def on_test_region_rectangle(img_bg, rect_xyxy, color, name, b_cropping_region=False,cropping_region_rect_xyxy=None):
    p1 = [rect_xyxy[0], rect_xyxy[1]]
    p2 = [rect_xyxy[2], rect_xyxy[3]]

    if b_cropping_region:
        p1[0] -= cropping_region_rect_xyxy[0]
        p1[1] -= cropping_region_rect_xyxy[1]
        p2[0] -= cropping_region_rect_xyxy[0]
        p2[1] -= cropping_region_rect_xyxy[1]

    cv2.rectangle(img_bg, tuple(p1), tuple(p2), color, 2, cv2.LINE_AA)
    cv2.putText(img_bg, name, tuple(p1), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 2)
    return img_bg

def on_test_region_polygon(img_bg, polygon_xys, color, name):
    p1 = [polygon_xys[0][0], polygon_xys[0][1]]
    points = []
    for i in range(len(polygon_xys)):
        x, y = polygon_xys[i]
        points.append([x, y])

    # 定义多边形的顶点坐标
    points = np.array(points, np.int32)

    # 调整数组形状以符合 cv2.polylines 和 cv2.fillPoly 的要求
    points = points.reshape((-1, 1, 2))

    cv2.polylines(img_bg, [points], True, color, 2, cv2.LINE_AA)

    cv2.putText(img_bg, name, tuple(p1), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 2)
    return img_bg






def calculate_circle_area(radius):
    """
    计算圆的面积

    参数:
    radius: 圆的半径

    返回:
    圆的面积
    """
    # 处理半径为负数的情况
    if radius < 0:
        raise ValueError("圆的半径不能为负数")

    # 使用公式: 面积 = π * 半径²
    return math.pi * (radius ** 2)


def calculate_ellipse_area(semi_major_axis, semi_minor_axis):
    """
    计算椭圆的面积

    参数:
    semi_major_axis: 椭圆的长半轴长度
    semi_minor_axis: 椭圆的短半轴长度

    返回:
    椭圆的面积
    """
    # 处理无效输入
    if semi_major_axis <= 0 or semi_minor_axis <= 0:
        raise ValueError("椭圆的长半轴和短半轴必须为正数")

    # 使用公式: 面积 = π * 长半轴 * 短半轴
    return math.pi * semi_major_axis * semi_minor_axis

def calculate_angle(A, B, C):
    """计算由三个点A、B、C形成的角ABC的度数"""
    # 计算向量BA和BC
    BA_x = A[0] - B[0]
    BA_y = A[1] - B[1]
    BC_x = C[0] - B[0]
    BC_y = C[1] - B[1]

    # 计算点积
    dot_product = BA_x * BC_x + BA_y * BC_y

    # 计算向量长度
    len_BA = math.sqrt(BA_x ** 2 + BA_y ** 2)
    len_BC = math.sqrt(BC_x ** 2 + BC_y ** 2)

    aa=(len_BA * len_BC)
    if aa==0:
        return 0
    # 计算余弦值
    cos_theta = dot_product / aa

    # 处理浮点数精度误差导致的余弦值超出[-1, 1]范围的情况
    cos_theta = max(-1.0, min(1.0, cos_theta))

    # 计算弧度和角度
    radian = math.acos(cos_theta)
    degree = math.degrees(radian)

    return degree


def is_point_in_rect(point, box_xyxy):
    """
    判断点是否在矩形内部

    参数:
    point (tuple): 点的坐标，格式为 (x, y)
    box_xyxy (tuple): 矩形的坐标，格式为 (x1, y1, x2, y2)
                  其中 (x1, y1) 是左下角坐标，(x2, y2) 是右上角坐标

    返回:
    bool: 如果点在矩形内部（包括边界）返回 True，否则返回 False
    """
    x, y = point
    x1, y1, x2, y2 = box_xyxy

    # 判断点的坐标是否在矩形的边界内
    return x1 <= x <= x2 and y1 <= y <= y2


#把方法标记为过时
def deprecated(message="此方法已弃用"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} 已弃用: {message}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_under_debugger():
    """
    检测调试器是否存在
    :return: true=调试模式，false=正常模式
    :rtype: bool
    """
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is None:
        return False
    else:
        v = gettrace()
        if v is None:
            return False
        else:
            return True

def is_point_in_rectangle(p, box_xyxy):
    """
    判断点 (px, py) 是否在矩形内（包含边界）。
    参数:
        px, py: 点的坐标
        x1, y1: 矩形左上角坐标
        x2, y2: 矩形右下角坐标
    返回:
        True 或 False
    """
    px,py=p
    x1, y1, x2, y2=box_xyxy
    return x1 <= px <= x2 and y1 <= py <= y2


def get_middle_point(A, B):
    """
    计算两点之间的中间点坐标

    参数:
    A (tuple): 第一个点的坐标，格式为 (x1, y1)
    B (tuple): 第二个点的坐标，格式为 (x2, y2)

    返回:
    tuple: 中间点的坐标，格式为 (x, y)
    """
    x = (A[0] + B[0]) / 2
    y = (A[1] + B[1]) / 2
    return (x, y)


def is_id_exists(two_d_array, target_id):
    """
    判断目标id是否存在于二维数组中

    参数:
        two_d_array: 格式为[[id, name], [id, name], ...]的二维数组
        target_id: 需要查找的id

    返回:
        布尔值，如果存在返回True，否则返回False
    """
    # 遍历二维数组中的每个元素
    for item in two_d_array:
        # 检查子数组的第一个元素是否为目标id
        if item[0] == target_id:
            return True
    # 遍历完所有元素都没找到，返回False
    return False


def is_valid_ip(ip_address):
    """
    验证IP地址是否合法

    参数:
        ip_address (str): 待验证的IP地址字符串

    返回:
        bool: 如果IP地址合法返回True，否则返回False
    """
    # 正则表达式模式
    # 解释:
    # 1. ^ 表示字符串开始
    # 2. (?:...) 表示非捕获组
    # 3. (25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?) 匹配0-255的数字
    #    - 25[0-5] 匹配250-255
    #    - 2[0-4][0-9] 匹配200-249
    #    - [01]?[0-9][0-9]? 匹配0-199，包括单个数字和两位数
    # 4. \. 匹配点号
    # 5. {3} 表示前面的组重复3次
    # 6. $ 表示字符串结束
    pattern = r'^(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    # 使用fullmatch检查整个字符串是否匹配模式
    return re.fullmatch(pattern, ip_address) is not None


def md5_encrypt(text):
    """
    对字符串进行MD5加密

    参数:
        text: 要加密的字符串

    返回:
        加密后的32位十六进制字符串
    """
    # 创建MD5对象
    md5_hash = hashlib.md5()

    # 更新MD5对象，需要将字符串转换为字节
    md5_hash.update(text.encode('utf-8'))

    # 获取加密后的十六进制字符串
    encrypted_text = md5_hash.hexdigest()

    return encrypted_text



def get_image_to_real_where( image_points, real_points):
    """
    将图像中足球的像素坐标转换为真实球框坐标系坐标
    获取条件透视变换的条件
    参数:

        image_points: 图像中4个参考点的像素坐标
        real_points: 对应参考点的真实世界坐标
    返回:
        足球在真实球框坐标系中的坐标 (X, Y)
    """
    if len(image_points) < 4:
        print('image_points 至少要4个坐标点')
        raise Exception('image_points 至少要4个坐标点')
        return None, None
    if len(real_points) < 4:
        print('real_points 至少要4个坐标点')
        raise Exception('real_points 至少要4个坐标点')
        return None, None
    if len(image_points) != len(real_points):
        print('image_points != real_points 数量')
        raise Exception('image_points != real_points 数量')
        return None, None

    # 转换为numpy数组格式
    image_points = np.array(image_points, dtype=np.float32)
    real_points = np.array(real_points, dtype=np.float32)

    # 计算透视变换矩阵 (图像坐标 -> 真实坐标)
    H, mask = cv2.findHomography(image_points, real_points, cv2.RANSAC, 5.0)

    # 输出有效内点数量（评估参考点质量）
    inlier_count = sum(mask.ravel() == 1)
    print(f"有效参考点数量: {inlier_count}/{len(image_points)}")
    if inlier_count < 4:
        print("警告：有效点不足4个，转换结果可能不可靠！")
    if inlier_count!=len(image_points):
        print("警告：有效参考点数量，比实际参考点数量要少, {}!={}，mask={}".format(inlier_count, len(image_points),str(mask).replace('\n','')))
        for i in range(len(mask)):
            item=mask[i]
            if item[0]!=1:
                print('警告：无效参考点是 {}，真实坐标是：{}，图像坐标是：{}'.format(i+1, real_points[i],image_points[i]))
    return H, mask


def get_image_to_real_where2( image_points, real_points):
    """
    将图像中足球的像素坐标转换为真实球框坐标系坐标
    获取条件透视变换的条件
    参数:

        image_points: 图像中4个参考点的像素坐标
        real_points: 对应参考点的真实世界坐标
    返回:
        足球在真实球框坐标系中的坐标 (X, Y)
    """
    if len(image_points) < 4:
        print('image_points 至少要4个坐标点')
        raise Exception('image_points 至少要4个坐标点')
        return None, None
    if len(real_points) < 4:
        print('real_points 至少要4个坐标点')
        raise Exception('real_points 至少要4个坐标点')
        return None, None
    if len(image_points) != len(real_points):
        print('image_points != real_points 数量')
        raise Exception('image_points != real_points 数量')
        return None, None

    # 现实坐标点（世界坐标，x范围0→9，y范围0→2.5）
    world_points = np.array(real_points, dtype=np.float32).reshape(-1, 1, 2)

    # 对应的图像坐标点（请再次确认每个现实点对应哪个图像点！）
    img_points = np.array(image_points, dtype=np.float32).reshape(-1, 1, 2)

    # ---------------------- 2. 优化单应性矩阵求解（关键改进）----------------------
    # 步骤1：先求「现实→图像」的H矩阵（现实点→图像点，分布规则，求解更准）
    H, mask = cv2.findHomography(
        srcPoints=world_points,  # 源：现实坐标
        dstPoints=img_points,  # 目标：图像坐标
        method=cv2.RANSAC,
        ransacReprojThreshold=2.0,  # 降低阈值，筛选更严格的内点
        confidence=0.995  # 提高置信度，减少外点影响
    )

    print("=== 现实→图像的单应性矩阵 H_world_to_img ===")
    print(H.round(4))
    print(f"内点数量：{np.sum(mask)} / 6（1=内点，0=外点）")

    # 步骤2：验证「现实→图像」的精度（关键！判断对应点是否正确）
    print("\n=== 验证：现实点→预测图像点（判断对应点是否匹配）===")
    for i in range(len(world_points)):
        # 用H矩阵将现实点转换为图像点
        pred_img_point = cv2.perspectiveTransform(world_points[i:i + 1], H)[0][0]
        true_img_point = img_points[i][0]
        # 像素误差（应<10像素，否则对应点错误）
        pixel_error = np.linalg.norm(pred_img_point - true_img_point)
        print(
            f"现实点 {world_points[i][0]} → 预测图像点 {pred_img_point.round(1)} | 真实图像点 {true_img_point} | 像素误差 {pixel_error:.1f}")

    # 步骤3：求H矩阵的逆，得到「图像→现实」的映射矩阵（核心修正！）
    # 只有当H矩阵可逆（行列式≠0）时有效（正常情况下成立）
    try:
        H = np.linalg.inv(H)
    except np.linalg.LinAlgError:
        raise ValueError("H矩阵不可逆，可能是对应点共线或匹配错误！")

    # 输出有效内点数量（评估参考点质量）
    inlier_count = sum(mask.ravel() == 1)
    print(f"有效参考点数量: {inlier_count}/{len(image_points)}")
    if inlier_count < 4:
        print("警告：有效点不足4个，转换结果可能不可靠！")
    if inlier_count!=len(image_points):
        print("警告：有效参考点数量，比实际参考点数量要少, {}!={}，mask={}".format(inlier_count, len(image_points),str(mask).replace('\n','')))
        for i in range(len(mask)):
            item=mask[i]
            if item[0]!=1:
                print('警告：无效参考点是 {}，真实坐标是：{}，图像坐标是：{}'.format(i+1, real_points[i],image_points[i]))
    return H, mask

def image_to_real_coords_by_H(football_pixel, H):
    """
    将图像中足球的像素坐标转换为真实球框坐标系坐标

    参数:
        football_pixel: 足球在图像中的像素坐标 (u, v)
        image_points: 图像中4个参考点的像素坐标
        real_points: 对应参考点的真实世界坐标
    返回:
        足球在真实球框坐标系中的坐标 (X, Y)
    """

    # 将足球像素坐标转换为齐次坐标
    u, v = football_pixel
    football_homogeneous = np.array([u, v, 1], dtype=np.float32).reshape(3, 1)

    # 应用透视变换
    real_homogeneous = H @ football_homogeneous

    # 归一化得到真实坐标
    w = real_homogeneous[2, 0]
    X = real_homogeneous[0, 0] / w
    Y = real_homogeneous[1, 0] / w

    return round(X, 2), round(Y, 2)

def image_to_real_coords(football_pixel, image_points, real_points):
    """
    将图像中足球的像素坐标转换为真实球框坐标系坐标

    参数:
        football_pixel: 足球在图像中的像素坐标 (u, v)
        image_points: 图像中4个参考点的像素坐标
        real_points: 对应参考点的真实世界坐标
    返回:
        足球在真实球框坐标系中的坐标 (X, Y)
    """
    if len(image_points) < 4:
        print('image_points 至少要4个坐标点')
        raise Exception('image_points 至少要4个坐标点')
        return None, None
    if len(real_points) < 4:
        print('real_points 至少要4个坐标点')
        raise Exception('real_points 至少要4个坐标点')
        return None, None
    if len(image_points) != len(real_points):
        print('image_points != real_points 数量')
        raise Exception('image_points != real_points 数量')
        return None, None

    # 转换为numpy数组格式
    image_points = np.array(image_points, dtype=np.float32)
    real_points = np.array(real_points, dtype=np.float32)

    # 计算透视变换矩阵 (图像坐标 -> 真实坐标)
    H, mask = cv2.findHomography(image_points, real_points, cv2.RANSAC, 5.0)

    # 输出有效内点数量（评估参考点质量）
    inlier_count = sum(mask.ravel() == 1)
    print(f"有效参考点数量: {inlier_count}/{len(image_points)}")
    if inlier_count < 4:
        print("警告：有效点不足4个，转换结果可能不可靠！")

    # 将足球像素坐标转换为齐次坐标
    u, v = football_pixel
    football_homogeneous = np.array([u, v, 1], dtype=np.float32).reshape(3, 1)

    # 应用透视变换
    real_homogeneous = H @ football_homogeneous

    # 归一化得到真实坐标
    w = real_homogeneous[2, 0]
    X = real_homogeneous[0, 0] / w
    Y = real_homogeneous[1, 0] / w

    return round(X, 2), round(Y, 2)

def get_y_center_symmetric_points(points):
    """
    计算点列表关于y坐标中心点对称的新坐标列表

    参数:
        points: 原始坐标列表，格式为[[x1, y1], [x2, y2], ...]

    返回:
        对称后的坐标列表和对称轴y值
    """
    # 提取所有y坐标
    y_coordinates = [y for x, y in points]

    # 计算y坐标的中心点（平均值）作为对称轴
    center_y = sum(y_coordinates) / len(y_coordinates)

    # 计算对称点
    symmetric_points = []
    for x, y in points:
        # 对称点的y坐标 = 2*中心点y坐标 - 原始y坐标
        symmetric_y = 2 * center_y - y
        symmetric_points.append([x, round(symmetric_y, 2)])  # 保留两位小数

    return symmetric_points, center_y


def is_point_in_rectangle_range(point, coordinates):
    """
    判断点是否在坐标列表所围成的矩形范围内

    参数:
        point: 待检查的坐标点，格式为[x, y]
        coordinates: 坐标点列表，格式为[[x1, y1], [x2, y2], ...]

    返回:
        bool: 点在范围内返回True，否则返回False
    """
    # 提取所有x坐标和y坐标
    x_coords = [coord[0] for coord in coordinates]
    y_coords = [coord[1] for coord in coordinates]

    # 计算x和y的最小值和最大值（矩形边界）
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    # 检查点是否在矩形范围内
    x, y = point
    return min_x <= x <= max_x and min_y <= y <= max_y


def is_point_in_polygon_handwriting(point, polygon):
    """
    使用射线法判断点是否在多边形内部

    参数:
        point: 待检查的点，格式为(x, y)
        polygon: 多边形顶点列表，格式为[(x1, y1), (x2, y2), ..., (xn, yn)]

    返回:
        bool: 点在多边形内返回True，否则返回False
    """
    # 先快速判断是否在矩形范围内，不在则直接返回False
    if not is_point_in_rectangle_range(point, polygon):
        return False

    x, y = point
    n = len(polygon)
    inside = False

    for i in range(n):
        # 获取多边形的一条边的两个端点
        p1x, p1y = polygon[i]
        p2x, p2y = polygon[(i + 1) % n]  # 最后一个点与第一个点相连

        # 检查点的y坐标是否在边的y范围内
        if ((p1y > y) != (p2y > y)):
            # 计算射线与边的交点x坐标
            x_intersect = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x

            # 如果点的x坐标小于交点x坐标，则射线与边相交
            if x < x_intersect:
                inside = not inside

    return inside


def mps_to_kmh(mps):
    """
    将米/秒转换为公里/小时

    参数:
    mps -- 以米/秒为单位的速度

    返回:
    转换后的以公里/小时为单位的速度
    """
    return mps * 3.6


def is_rolling_up_down(coords, threshold=2,where_drop=None,where_count=3):
    """
    判断足球轨迹是否存在上下滚动动作

    参数：
        coords：列表，元素为(x,y)元组，代表足球的轨迹坐标
        threshold：阈值，用于过滤微小波动，默认值为2
        where_drop：y坐标落差，大于足球的尺寸就可以了
        where_count: 上下滚动动作 次数
    返回：
        bool：True表示存在上下滚动，False表示不存在
    """
    # 至少需要2个点才能判断趋势
    if len(coords) < 2:
        return False

    # 提取y坐标序列
    y_list = [y for x, y in coords]

    if where_drop:
        y_drop=max(y_list)-min(y_list)
        if y_drop<where_drop:
            return False#y 坐标落差不符合

    # 计算相邻y值的差值（dy）
    dy_list = [y_list[i + 1] - y_list[i] for i in range(len(y_list) - 1)]

    # 根据阈值判断每个dy的趋势（1：上升，-1：下降，0：平稳）
    trends = []
    for dy in dy_list:
        if dy > threshold:
            trends.append(1)
        elif dy < -threshold:
            trends.append(-1)
        else:
            trends.append(0)

    # 合并连续相同的趋势，得到阶段列表
    if not trends:
        stages = []
    else:
        stages = [trends[0]]
        for t in trends[1:]:
            if t != stages[-1]:
                stages.append(t)

    # 若阶段中同时存在上升（1）和下降（-1），则存在上下滚动
    has_up = 1 in stages
    has_down = -1 in stages
    state=has_up and has_down
    if not state:
        return state
    dic_trends_count={}
    for item in trends:
        if item in dic_trends_count:
            dic_trends_count[item]=dic_trends_count[item]+1
        else:
            dic_trends_count[item]=1
    count=0
    for key,item in dic_trends_count.items():
        if item>where_count:
            count+=1

    if count>=2:
        state=True
    else:
        state=False
    return state

def mps_to_kmh(mps):
    """
    将米/秒转换为公里/小时

    参数:
    mps -- 以米/秒为单位的速度

    返回:
    转换后的以公里/小时为单位的速度
    """
    return mps * 3.6

#对比图片，判断是否有变化，背景是否移动了
def get_bg_moving_state(img_gray1,img_gray2,img_w,img_h,min_thresh = 20,MOTION_PIXEL_RATIO = 0.1,box_a=None,box_frame_xyxy=None,list_box_person=None):
    """
    对比图片，判断是否有变化，背景是否移动了
    Args:
        img_gray1: 图片1
        img_gray2: 图片2
        img_w: 宽度
        img_h: 高度
        min_thresh: 分阈值（越小越灵敏）
        MOTION_PIXEL_RATIO: ROI内运动像素占比阈值（超过则判定网动）
        box_a: box的面积，要减去
    Returns:
    state,motion_ratio
    """
    if box_a is None:
        box_a=0
    state=False
    if img_gray1.shape[0]!=img_h or img_gray1.shape[1]!=img_w:
        #缩放
        # print('img_gray1 cv2.resize=',img_w, img_h)
        img_gray1 = cv2.resize(img_gray1, (img_w, img_h))
    if img_gray2.shape[0]!=img_h or img_gray2.shape[1]!=img_w:
        #缩放
        # print('img_gray2 cv2.resize=',img_w, img_h)
        img_gray2 = cv2.resize(img_gray2, (img_w, img_h))
    # 4.1 帧间差分：计算当前ROI与上一帧ROI的像素差
    frame_diff = cv2.absdiff(img_gray1, img_gray2)
    # 4.2 阈值化：只保留明显的像素变化（过滤噪声）
    _, diff_thresh = cv2.threshold(frame_diff, min_thresh, 255, cv2.THRESH_BINARY)
    # 4.3 排除干扰：减去足球区域的掩码（足球穿过ROI时不误判）
    # diff_thresh = cv2.subtract(diff_thresh, football_mask)
    if box_frame_xyxy is not None and list_box_person is not None and len(list_box_person)>0:
        #擦除人的区域
        for item_box_person in list_box_person:
            box_xyxy_person=item_box_person.get_xyxy()
            b_intersect=is_rectangle_intersect_by_xyxy(box_frame_xyxy,box_xyxy_person)
            if not b_intersect:
                continue#不相交
            box_xyxy_person[0] = box_xyxy_person[0] - box_frame_xyxy[0]
            box_xyxy_person[1] = box_xyxy_person[1] - box_frame_xyxy[1]
            box_xyxy_person[2] = box_xyxy_person[2] - box_frame_xyxy[0]
            box_xyxy_person[3] = box_xyxy_person[3] - box_frame_xyxy[1]
            p1=(box_xyxy_person[0],box_xyxy_person[1])
            p2=(box_xyxy_person[2],box_xyxy_person[3])
            # cv2.imwrite('diff_thresh_rectangle1.jpg', diff_thresh)
            roi=cv2.rectangle(diff_thresh,p1,p2,(0),-1,cv2.LINE_AA)
            # cv2.imwrite('diff_thresh_rectangle2.jpg', roi)
            pass
    # 4.4 形态学降噪：去除小噪声点（网动是细小分散的，不影响）
    diff_thresh = cv2.erode(diff_thresh, np.ones((3, 3), np.uint8), iterations=1)
    diff_thresh = cv2.dilate(diff_thresh, np.ones((3, 3), np.uint8), iterations=1)

    # 4.5 统计运动像素占比
    total_pixels = img_w * img_h
    motion_pixels = cv2.countNonZero(diff_thresh)-box_a
    motion_ratio = motion_pixels / total_pixels
    if motion_ratio > MOTION_PIXEL_RATIO:
        state=True
    return state,motion_ratio,diff_thresh


def open_folder(folder_path):
    """
    跨平台打开文件夹窗口
    :param folder_path: 文件夹路径（绝对/相对路径均可）
    :return: 成功返回True，失败返回False
    """
    # 先校验文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹不存在 → {folder_path}")
        return False

    # 确保路径是绝对路径（避免跨平台路径解析问题）
    folder_path = os.path.abspath(folder_path)
    print(f"正在打开文件夹 → {folder_path}")

    try:
        # 根据操作系统选择打开方式
        system = platform.system()
        if system == "Windows":
            # Windows：使用os.startfile（原生无黑窗）
            os.startfile(folder_path)
        elif system == "Darwin":  # macOS
            # macOS：使用open命令
            subprocess.call(["open", folder_path])
        elif system == "Linux":
            # Linux：使用xdg-open命令（兼容绝大多数发行版）
            subprocess.call(["xdg-open", folder_path])
        else:
            print(f"错误：不支持的操作系统 → {system}")
            return False
        return True
    except Exception as e:
        print(f"打开文件夹失败 → {e}")
        return False

if __name__ == '__main__':

    all_ips = get_all_ip_addresses()
    print("电脑的所有 IP 地址如下:")
    for ip in all_ips:
        print(ip)

    # monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
    # print('monitor info:{}'.format(monitor_info))  # 监视器信息
    # monitor = monitor_info.get('Monitor')  # 屏幕分辨率
    # print('屏幕分辨率:{}'.format(monitor))
    # work = monitor_info.get('Work')  # 工作区间
    # print('工作区间:{}'.format(work))
    # print('任务栏高度:{}'.format(monitor[3] - work[3]))  # 任务栏高度
    #
    # # 获取屏幕尺寸
    # screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    # screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    #
    # # 获取任务栏尺寸（这里假设任务栏在屏幕的底部）
    # taskbar_height = win32api.GetSystemMetrics(win32con.SM_CYBORDER) + win32api.GetSystemMetrics(
    #     win32con.SM_CYSIZE) + win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
    # print(taskbar_height)
    # pass
    # print(get_window_taskbar_height())
    #
    # # 132844
    # win32Window: Win32Window = get_Win32Window(132844)
    # print(win32Window)

    # 测试 IP 地址
    ip = '192.168.1.123'
    if is_ip_reachable(ip):
        print(f"{ip} 可以连通。")
    else:
        print(f"{ip} 无法连通。")

    format_string = "%Y-%m-%d %H:%M:%S"
    t=time.time()
    time_string = get_str_time_by_file(t,fmt=format_string)

    timestamp = string_to_timestamp(time_string, format_string)
    if timestamp is not None:
        print(f"时间戳: {timestamp}")

    print('t=',t,'timestamp=',timestamp,'time_string=',time_string)

