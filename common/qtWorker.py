import time

from PySide6.QtCore import QThread, Signal

from common.setting import ImgColorType




class WorkerDataFraCameraManage(object):
    def __init__(self):
        self.img_cv = None
        self.qpixmap=None
        self.frame_count = 0
        self.img_color_type:ImgColorType=ImgColorType.none

class WorkerStateMsg(object):
    def __init__(self,state,msg):
        self.state=state
        self.msg=msg

#qt 主线程运行 基础类
class WorkerManageBase(QThread):
    update_ui = Signal(WorkerStateMsg)  # 定义一个信号，用于向主线程发送需要更新的内容
    def __init__(self,time_sleep=0.01):
        super().__init__()
        self.b_update_state = False
        self.data= None
        self.time_sleep=time_sleep
        self.b_close=False
        self.b_start = False


    def start(self, priority=None):
        if self.b_start is True:
            return #不用重复打开
        self.b_start = True
        self.b_close = False
        # self.started.emit()
        super().start()

    def on_set_update_date(self, data):
        self.data = data
        self.b_update_state = True

    def on_close(self):
        if self.b_close is True:
            return
        self.b_start = False
        self.b_close=True
        super().requestInterruption()  # 请求线程中断
        super().quit()  # 退出事件循环
        super().wait()  # 等待线程结束

    def run(self):
        if self.b_start is False:
            self.finished.emit()  # 工作完成时发送信号
            return
        if self.b_close is True:
            self.finished.emit()  # 工作完成时发送信号
            return
        # print('Worker QThread run：',self.__class__.__name__)
        while self.b_close is False and self.b_start is True:
            if self.isInterruptionRequested():
                return
            if self.b_update_state is True:
                self.b_update_state = False
                self.update_ui.emit(self.data)  # 当有结果时，触发信号发送给主线程
            time.sleep(self.time_sleep)
        self.finished.emit()  # 工作完成时发送信号
        # print('Worker QThread end：', self.__class__.__name__)


# QT 界面更新线程
class WorkerStateMsgTarget(WorkerManageBase):
    update_ui = Signal(WorkerStateMsg)  # 定义一个信号，用于向主线程发送需要更新的内容


class WorkerFraCameraManage1(WorkerManageBase):
    update_ui = Signal(WorkerDataFraCameraManage)  # 定义一个信号，用于向主线程发送需要更新的内容


class WorkerFraCameraManage2(WorkerManageBase):
    update_ui = Signal(WorkerDataFraCameraManage)  # 定义一个信号，用于向主线程发送需要更新的内容



