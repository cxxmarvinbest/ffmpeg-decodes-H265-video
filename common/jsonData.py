# 发送的类型
import os
import time
import json
from decimal import Decimal

import numpy as np


# json 转换格式处理类
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.int64):
            return str(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bytes):
            return str(obj)
        elif isinstance(obj,Decimal):
            return float(obj)
        else:
            return super(NpEncoder, self).default(obj)

#消息类型
class BaseType:
    # 文本消息，互相发送
    Text = 0
    # 心跳包
    Heartbeat = 1
    # 服务端发给客户端，连接成功
    ConnectSuccess = 11
    # 客户端发给服务端，客户端标识
    ClientIdentification = 12
    # 服务端发给客户端，验证标识
    VerificationStatus = 13
    # 服务端发给客户端，说服务端要关闭了
    ServerClose = 15
    # 客户端发给服务端，说客户端要关闭了
    ClientClose = 16
    # 服务端发给客户端，说指定关闭你客户端
    CloseClient = 17

    #客户端发送检测数据
    Client_Send_Detect_Data = 30


    #服务器推送给客户端通知可以更新数据了
    server_send_update_data_to_client = 40



# 基本类
class BaseData:
    def __init__(self, msgType=None, sendData=None, now_time=None):
        self.msgType = msgType
        self.data = sendData
        if now_time is None:
            now_time = time.time()
        self.time = now_time


# 发送数据
class SendData:
    def __init__(self, text=None, obj=None):
        self.text = text
        self.obj = obj


# json字符串 转 类对象
def json_to_obj(jsonData):
    obj = json.loads(jsonData)
    return obj


# 类对象  转 json字符串
def obj_to_json(obj,indent=None):
    jsonData = json.dumps(obj, ensure_ascii=False, cls=NpEncoder, indent=indent)
    return jsonData


# 把Object对象转换成Dict对象
def convert_to_dict(obj):
    '''把Object对象转换成Dict对象'''
    dict = {}
    dict.update(obj.__dict__)
    return dict


# 获取发送数据，返回json字符串
def get_send_data_to_json(msgType, text='', obj=None, now_time=None):
    mySendData = {'text': text, 'obj': obj}
    if now_time is None:
        now_time = time.time()
    myBaseData = {'msgType': msgType, 'data': mySendData, 'time': now_time}
    jsonData = obj_to_json(myBaseData)
    return jsonData


def get_send_data_to_json2(msgType, text='', obj=None, now_time=None):
    mySendData = SendData(text, obj)
    mySendData_dict = convert_to_dict(mySendData)
    myBaseData = BaseData(msgType, sendData=mySendData_dict, now_time=now_time)
    myBaseData_dict = convert_to_dict(myBaseData)
    jsonData = obj_to_json(myBaseData_dict)
    return jsonData


# 获取发送数据，返回 类对象
def get_send_data_to_obj(msgType, text='', obj=None, now_time=None):
    mySendData = SendData(text, obj)
    mySendData_dict = convert_to_dict(mySendData)
    myBaseData = BaseData(msgType, sendData=mySendData_dict, now_time=now_time)
    return myBaseData


#读取json数据
def get_json_data(path):
    if os.path.exists(path) is False:
        return None
    json_data=None
    with open(path, 'r', encoding='utf8') as fp:
        text=fp.read()
        if text is not None and text!='':
            json_data = json.loads(text)
    return json_data

#保存json数据
def save_json_data(path,text):
    if isinstance(text, str) is False:
        #转换成文本再保存
        text = json.dumps(text, ensure_ascii=False, cls=NpEncoder, indent=1)
    # 创建
    with open(path, 'w', encoding='utf8') as fp:
        fp.write(text + '\n')

def json_to_str(json_data,indent=None):
    text = json.dumps(json_data, ensure_ascii=False, cls=NpEncoder, indent=indent)
    return text
