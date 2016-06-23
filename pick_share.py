# coding=utf-8

from datetime import datetime, timedelta
import time
import threading
import Queue
import sys
import tushare as ts
DELTA_DATE = 5
LIMIT = 9.95
with open("shares.txt") as f:
    SHARES = f.readlines()
SHARES = map(str.strip, SHARES)


def get_start_date(day_delta):
    end_date = datetime.now()
    delta = timedelta(days=day_delta)
    start = (end_date - delta).strftime('%Y-%m-%d')
    return start


def decline(dict_data):
    volume = dict_data["volume"]
    open = dict_data["open"]
    close = dict_data["close"]
    p_change = dict_data["p_change"]

    # 不考虑停牌的情况
    if len(volume) < DELTA_DATE:
        return ""

    # case2 前三天持续缩量下跌，且第一天是下跌，绿柱实体至少一个点，第二天也下跌，第四天放量翻红
    i = 0
    if (open[i + 3] - close[i + 3]) / close[i + 3] > 0.01:
        if volume[i + 3] > volume[i + 2] > volume[i + 1] < volume[i]:
            if open[i + 3] > close[i + 3] > close[i + 2] > close[i + 1] and open[i + 2] > close[i + 2] \
                    and close[i] > max(open[i], open[i + 1], close[i + 1]):
                return "case2"

    # case1 最近三天持续缩量下跌，且第一天是下跌，绿柱实体至少一个点，且收盘价持续下降
    if (open[2] - close[2]) / close[2] > 0.01:
        if volume[2] > volume[1] > volume[0]:
            if open[2] > close[2] > close[1] > close[0] and open[1] > close[1]:
                return "case1"

    # 收盘连续两天跌停，加关注
    if p_change[0] < -LIMIT > p_change[1]:
        return "case3"
    return ""


def test(share):
    data = ts.get_hist_data(share, '2014-06-23')
    dict_data = data.to_dict('list')
    all_data = data.to_dict('dict')
    dates = []
    volume = dict_data["volume"]
    open = dict_data["open"]
    close = dict_data["close"]
    for i in range(len(dict_data["volume"]) - 3):
        try:
            # case2 前三天持续缩量下跌，且第一天是下跌，绿柱实体至少一个点，第二天也下跌，第四天放量翻红
            if (open[i + 3] - close[i + 3]) / close[i + 3] > 0.01:
                if volume[i + 3] > volume[i + 2] > volume[i + 1] < volume[i]:
                    if open[i + 3] > close[i + 3] > close[i + 2] > close[i + 1] and open[i + 2] > close[i + 2] \
                            and close[i] > max(open[i], open[i + 1], close[i + 1]):

                        volume_values = all_data["volume"].values()
                        if volume_values.count(volume[i]) == 1:
                            date = all_data["volume"].keys()[volume_values.index(volume[i])]
                            dates.append(date)
                            continue
                        dates.append(i)
        except:
            continue
    if dates:
        print share, dates


class WorkManager(object):
    def __init__(self, thread_num=24):
        self.work_queue = Queue.Queue()
        self.threads = []
        self.__init_work_queue()
        self.__init_thread_pool(thread_num)

    def __init_thread_pool(self, thread_num):
        for i in range(thread_num):
            self.threads.append(Work(self.work_queue))

    def __init_work_queue(self):
        for share in SHARES:
            # 任务入队，Queue内部实现了同步机制
            self.work_queue.put((test, share))

    def wait_allcomplete(self):
        for item in self.threads:
            if item.isAlive():
                item.join()


class Work(threading.Thread):
    def __init__(self, work_queue):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.start()

    def run(self):
        # 死循环，从而让创建的线程在一定条件下关闭退出
        while True:
            try:
                do, args = self.work_queue.get(block=False)  # 任务异步出队，Queue内部实现了同步机制
                do(args)
                self.work_queue.task_done()  # 通知系统任务完成
            except:
                break


if __name__ == '__main__':
    start = get_start_date(DELTA_DATE + 1)
    # print start, end
    # shares = ["600005"]
    select_shares = {"case1": [], "case2": []}
    # t1 = time.time()
    # for share in shares:
    #     data = ts.get_hist_data(share, start)
    #     # print data
    #     try:
    #         dict_data = data.to_dict('list')
    #         ret = decline(dict_data)
    #         if ret:
    #             select_shares[ret].append(share)
    #             print share, ret
    #     except AttributeError:
    #         continue
    # # print select_shares
    # # for key in select_shares:
    # #     print len(select_shares[key])
    # t2 = time.time()
    # print "cost {} seconds".format(t2 - t1)
    # sys.exit()

    # t1 = time.time()
    # for share in SHARES:
    #     data = ts.get_hist_data(share, '2014-06-23')
    #     try:
    #         dates = test(data)
    #         if dates:
    #             print share, dates
    #     except AttributeError:
    #         continue
    # t2 = time.time()
    # print "cost {} seconds".format(t2 - t1)
    #
    work_manager = WorkManager()
    work_manager.wait_allcomplete()

#             open   high  close    low     volume  price_change  p_change  \
# date
# 2016-06-21  17.88  17.95  17.81  17.75  158528.73         -0.04     -0.22
# 2016-06-20  17.93  17.93  17.86  17.75   96814.95          0.09      0.51
# 2016-06-17  17.75  17.99  17.79  17.74  174122.33         -0.01     -0.06
# 2016-06-16  17.67  17.93  17.80  17.60  308711.28          0.06      0.34
#
#                ma5    ma10    ma20      v_ma5     v_ma10     v_ma20  turnover
# date
# 2016-06-21  17.804  17.863  17.865  200299.81  207123.38  187827.34      0.08
# 2016-06-20  17.802  17.884  17.847  206140.78  209274.02  185471.22      0.05
# 2016-06-17  17.784  17.901  17.822  246880.96  217379.05  185820.88      0.09
# 2016-06-16  17.826  17.942  17.807  259573.09  218279.24  192595.99      0.17
#
# [4 rows x 14 columns]

#
# Definition: data.to_dict(self, outtype='dict')
# Docstring:
# Convert DataFrame to dictionary.
#
# Parameters
# ----------
# outtype : str {'dict', 'list', 'series', 'records'}
#     Determines the type of the values of the dictionary. The
#     default `dict` is a nested dictionary {column -> {index -> value}}.
#     `list` returns {column -> list(values)}. `series` returns
#     {column -> Series(values)}. `records` returns [{columns -> value}].
#     Abbreviations are allowed.
#
#
# Returns
# -------
# result : dict like {column -> {index -> value}}
