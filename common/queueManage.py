from queue import Queue, LifoQueue

#队列管理器
class QueueManage(object):
    def __init__(self, queue_type=1, maxsize=99999, get_timeout=None, put_timeout=None, put_block=True, get_block=True):
        self.get_timeout = get_timeout
        self.put_timeout = put_timeout
        self.put_block = put_block
        self.get_block = get_block
        # 先进先出队列
        if queue_type == 1:
            # 先进先出队列
            self.my_queue:Queue = Queue(maxsize=maxsize)

        elif queue_type == 2:
            # 后进先出队列
            self.my_queue:LifoQueue = LifoQueue(maxsize=maxsize)

    # 写入队列
    def put(self, value):
        state, msg,get_value = False, '',None
        try:
            bfull = self.my_queue.full()  # 判断是否满了
            if bfull is True:
                # 已经满了，只能先取一个出来
                get_value=self.my_queue.get()
                # print('队列已经满了，只能先取一个出来'+str(get_value))
            self.my_queue.put(value, block=self.put_block, timeout=self.put_timeout)  # 添加
            state = True
        except Exception as ex:
            msg = str(ex)
        return state, msg,get_value

    # 获取队列
    def get(self):
        state, value, msg = False, None, ''
        try:
            if self.get_block is False:
                empty = self.my_queue.empty()  # 是否为空
                if empty is True:
                    return state, value, msg
                qsize = self.my_queue.qsize()  # 大小
                if qsize <= 0:
                    return state, value, msg
            value = self.my_queue.get(block=self.get_block, timeout=self.get_timeout)
            if value is None:
                msg = '获取的数据为空'
            else:
                state = True
        except Exception as ex:
            msg = str(ex)
        return state, value, msg

    #获取队列大小
    def get_size(self):
        state, qsize,msg = False, 0,''
        try:
            empty = self.my_queue.empty()  # 是否为空
            if empty is True:
                return state, qsize,msg
            qsize = self.my_queue.qsize()  # 大小
            if qsize <= 0:
                return state, qsize,msg
            state=True
        except Exception as ex:
            msg=str(ex)
        return state, qsize,msg

    #获取时候为空
    def get_empty(self):
        state, empty,msg = False, False,''
        try:
            empty = self.my_queue.empty()  # 是否为空
            state=True
        except Exception as ex:
            msg=str(ex)
        return state, empty,msg

    #清空队列
    def clear(self):
        state,msg=False,''
        try:
            empty = self.my_queue.empty()  # 是否为空
            if empty is True:
                msg='已经为空'
                return state,msg
            qsize = self.my_queue.qsize()  # 大小
            if qsize <= 0:
                msg = '已经为空'
                return state, msg
            #没有清空的方法，只能全部都取出来了
            for i in range(qsize):
                value = self.my_queue.get()
            empty = self.my_queue.empty()  # 是否为空
            qsize = self.my_queue.qsize()  # 大小
            state=True
        except Exception as ex:
            msg=str(ex)
        return msg

    #判断是否为空，没有数量
    @property
    def is_null(self):
        state, qsize,msg=self.get_size()
        return state is False or qsize<=0

    #直接获取数量
    @property
    def count(self):
        state, qsize,msg=self.get_size()
        return qsize