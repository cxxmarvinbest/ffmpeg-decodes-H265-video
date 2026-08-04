
# 日志库

import logging
import logging.handlers
import os
import datetime as dt
import time
from colorama import init, Fore, Back, Style

# 初始化 colorama
init(autoreset=True)

# 创建一个自定义的格式化器
class ColoredFormatter(logging.Formatter):
    # 定义不同日志级别的颜色
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Back.WHITE
    }

    def format(self, record):
        # 获取日志记录的级别
        log_color = self.COLORS.get(record.levelno)
        # 应用颜色到日志消息
        formatted = super().format(record)
        return log_color + formatted + Style.RESET_ALL

class logs(object):
    def __init__(self, name=None, int_path_formatter_type=1,is_save_file=True,log_level_stream='INFO',log_level_file='INFO'):
        if name is None:
            name = __name__
        self.name = name
        self._tempLog = ''
        self.logger: logging.Logger | None = None
        self.str_now_path = ''
        self.str_now_path2 = ''
        self.all_file_path = ''
        self.is_save_file=is_save_file
        # logger 输出格式
        self.formatter_file = logging.Formatter('%(name)s->%(asctime)s - %(levelname)s - %(message)s')  # %(name)s
        self.formatter_stream = ColoredFormatter('%(name)s->%(levelname)s - %(asctime)s: %(message)s')#logging.Formatter('%(levelname)s - %(asctime)s: %(message)s')  # %(name)s
        self.formatter_stream.formatTime = self.sim_time
        self.addHandlers = []
        if int_path_formatter_type is None or int_path_formatter_type is not [1, 2, 3]:
            int_path_formatter_type = 1
        self.int_path_formatter_type = int_path_formatter_type  # 目录格式类型，1=年月日，2=年月日时，3=年月日时分
        self.level_stream=logging.INFO
        self.level_file = logging.INFO
        if log_level_stream is not None and isinstance(log_level_stream,str):
            if log_level_stream=='DEBUG':
                self.level_stream = logging.DEBUG
            elif log_level_stream=='INFO':
                self.level_stream = logging.INFO
            elif log_level_stream=='WARN':
                self.level_stream = logging.WARN
            elif log_level_stream=='ERROR':
                self.level_stream = logging.ERROR
        elif log_level_stream is not None and isinstance(log_level_stream,int):
            self.level_stream = log_level_stream
        if log_level_file is not None and isinstance(log_level_stream,str):
            if log_level_file=='DEBUG':
                self.level_file = logging.DEBUG
            elif log_level_file=='INFO':
                self.level_file = logging.INFO
            elif log_level_file=='WARN':
                self.level_file = logging.WARN
            elif log_level_file=='ERROR':
                self.level_file = logging.ERROR
        elif log_level_file is not None and isinstance(log_level_file,int):
            self.level_file = log_level_file
        self.level_logger=min(self.level_stream,self.level_stream)
        self.load_log(self.name)


    # 自定义时间
    def sim_time(self, record, datefmt=None):
        return dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    # 初始化日志
    def load_log(self, name):
        self._tempLog = ''
        self.logger = logging.getLogger(name)
        self.logger.propagate = False
        # 以下三行为清空上次文件
        # 这为清空当前文件的logging 因为logging会包含所有的文件的logging
        logging.Logger.manager.loggerDict.pop(name)
        # 将当前文件的handlers 清空
        self.logger.handlers = []

        # 然后再次移除当前文件logging配置
        self.logger.removeHandler(self.logger.handlers)

        #  这里进行判断，如果logger.handlers列表为空，则添加，否则，直接去写日志
        self.str_now_path = self.get_log_new_path(is_sys_path=False)
        self.str_now_path2 = os.getcwd() + self.str_now_path
        if not os.path.exists(self.str_now_path2):
            os.makedirs(self.str_now_path2)
        self.all_file_path = self.str_now_path2 + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())) + '.log'
        if not self.logger.handlers:
            # loggger 文件配置路径
            self.fleHandler = logging.FileHandler(self.all_file_path, encoding='utf-8')

            self.streamHandler = logging.StreamHandler()

            # logger 配置等级
            self.logger.setLevel(self.level_logger)

            self.fleHandler.setLevel(self.level_file)
            self.streamHandler.setLevel(self.level_stream)

            # 添加输出格式进入handler
            self.fleHandler.setFormatter(self.formatter_file)
            self.streamHandler.setFormatter(self.formatter_stream)
            # 添加文件设置金如handler
            if self.is_save_file is True:
                self.logger.addHandler(self.fleHandler)
            self.logger.addHandler(self.streamHandler)
            self.addHandlers = self.logger.handlers

    # 获取新的目录
    def get_log_new_path(self, is_sys_path=False):
        # str_time=str(dt.date.today())
        if self.int_path_formatter_type == 1:
            # 年月日
            str_time = str(time.strftime("%Y-%m-%d", time.localtime()))
        elif self.int_path_formatter_type == 2:  # 年月日时
            str_time = str(time.strftime("%Y-%m-%d_%H", time.localtime()))  #
        elif self.int_path_formatter_type == 3:  # 年月日时分
            str_time = str(time.strftime("%Y-%m-%d_%H-%M", time.localtime()))  #
        else:
            # 年月日
            str_time = str(time.strftime("%Y-%m-%d", time.localtime()))
        str_path = '/logs/' + str_time + '/'  # _log
        if is_sys_path is True:
            str_path = os.getcwd() + str_path
        return str_path

    # def update_handler(self):
    #     logger2 = logging.getLogger()
    #     if logger2 is not None and logger2.name is not self.name:
    #         addHandlers3 = logger2.handlers
    #         if len(addHandlers3) > 0:
    #             for i in range(len(addHandlers3)):
    #                 addHandlers3[i].setLevel(logging.WARNING)
    #         logger2.setLevel(logging.WARNING)

    # 更新日志保存的目录
    def update_file_path(self):
        # self.load_log(self.name)
        if self.is_save_file is False:
            return
        self.fleHandler.close()  # 关闭保存上次的
        self.logger.removeHandler(self.fleHandler)  # 移除上一次的
        self.str_now_path = self.get_log_new_path(is_sys_path=False)
        self.str_now_path2 = os.getcwd() + self.str_now_path
        if not os.path.exists(self.str_now_path2):
            os.makedirs(self.str_now_path2)
        self.all_file_path = self.str_now_path2 + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())) + '.log'
        self.fleHandler = logging.FileHandler(self.all_file_path, encoding='utf-8')
        self.fleHandler.setFormatter(self.formatter_stream)
        self.fleHandler.setLevel(self.level_file)
        self.logger.addHandler(self.fleHandler)

    def info(self, *message):
        if self.level_stream>logging.INFO and self.level_file>logging.INFO:
            return
        if self._tempLog == message:
            return  # 过滤打印重复数据
        str_path = self.get_log_new_path(is_sys_path=False)
        if str_path != self.str_now_path:
            # 不同一天了
            self.update_file_path()
        self.logger.info(message)
        self._tempLog = message

    def debug(self, *message):
        if self.level_stream > logging.DEBUG and self.level_file > logging.DEBUG:
            return
        str_path = self.get_log_new_path(is_sys_path=False)
        if str_path != self.str_now_path:
            # 不同一天了
            self.load_log(self.name)
        self.logger.debug(str(message))

    def warning(self, *message):
        if self.level_stream > logging.WARN and self.level_file > logging.WARN:
            return
        str_path = self.get_log_new_path(is_sys_path=False)
        if str_path != self.str_now_path:
            # 不同一天了
            self.load_log(self.name)
        self.logger.warning(str(message))

    def error(self, *message):
        if self.level_stream > logging.ERROR and self.level_file > logging.ERROR:
            return
        str_path = self.get_log_new_path(is_sys_path=False)
        if str_path != self.str_now_path:
            # 不同一天了
            self.load_log(self.name)
        self.logger.error(str(message))



if __name__ == "__main__":
    my_log = logs('AI')
    while True:
        my_log.info('测试0')
        my_log.info('测试1', '测试2', time.time())
        my_log.debug('测试1', '测试2', time.time())
        my_log.warning('测试1', '测试2', time.time())
        my_log.error('测试1', '测试2', time.time())
        time.sleep(2)
