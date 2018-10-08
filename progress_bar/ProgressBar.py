import sys
import time


class ProgressBar:
    """ 进度条 """

    # 指示器(菊花)的字符
    activity_indicator_chars = ['-', '\\', '|', '/']
    # 其余剩余字符长度
    other_length = 54

    # 配置信息
    options = None

    def __init__(self, options = None):
        # 检查参数
        if options is None:
            options = ProgressBarOptions()
        # 设置配置
        self.options = options

        # 整理配置
        self.options.char = ProgressBarOptions.char if (self.options.char is None or len(self.options.char) == 0) else \
            self.options.char[0]
        self.options.empty_char = ProgressBarOptions.empty_char if \
            (self.options.empty_char is None or len(self.options.empty_char) == 0) else self.options.empty_char[0]
        self.options.count = ProgressBarOptions.count if \
            (self.options.count is None or isinstance(self.options.count, int) is not True or self.options.count <= 0) \
            else self.options.count

        # 初始化数据
        self.transferred_log = {}       # 上传记录; k: 上传时间, v: 上传的bytes
        self.last_transferred = 0       # 上次上传了的字节数量
        self.update_count = 0           # 更细进度条的次数

        # 输出占位符
        print(' ' * (self.options.count + self.other_length), end='')

    def update(self, transferred, total):
        """ 更新进度条 """

        # 计算完成比例
        percent = int(transferred / total * 100)
        # 根据完成比例计算进度条长度(数量)
        charcount = int(percent / 100 * self.options.count)

        # 上一秒发送的字节数量, 当前时间
        transferred_in_last_second, now = 0, time.time()
        # 计算上一秒发送的字节数量
        for k in list(self.transferred_log.keys())[::-1]:
            if (now - k) < 1:
                transferred_in_last_second += self.transferred_log[k]

        # 输出进度条
        sys.stdout.write(
            # 删除之前显示的长度
            '\b' * (self.options.count + self.other_length) + \
            # 菊花
            ('-' if percent == 100 else self.activity_indicator_chars[self.update_count % 4]) + \
            '[' + \
            # 百分比
            (str(percent).rjust(3, ' ')) + '%: ' + \
            # 进度条
            (self.options.char * charcount) + (self.options.empty_char * (self.options.count - charcount)) + ': ' + \
            # 上传大小 / 剩余大小
            ((self.readable_bytes(transferred).rjust(10, ' ',) + '/') if percent != 100 else '') + \
            self.readable_bytes(total).rjust(10 if percent != 100 else 21, ' ') + \
            ']' + \
            ((' ' * 22) if percent == 100 else (
                # 上传速度
                (self.readable_bytes(transferred_in_last_second).rjust(10, ' ') + '/s') +
                # 剩余时间
                ' eta' + ('N/A' if transferred_in_last_second == 0 else self.readable_seconds((total - transferred) / transferred_in_last_second)).rjust(6, ' ') \
            ))
        )
        sys.stdout.flush()

        # 添加记录
        if now in self.transferred_log.keys():
            self.transferred_log[now] += transferred - self.last_transferred
        else:
            self.transferred_log[now] = transferred - self.last_transferred
        self.last_transferred = transferred

        # 更新计数
        self.update_count += 1

    # 字节长度单位
    bytes_units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

    @classmethod
    def readable_bytes(cls, c):
        """ 整理字节长度, 优化人类阅读 """

        # 单位下标
        i = 0
        while c >= 1024:
            i += 1
            if i >= len(cls.bytes_units):
                return '>1024' + cls.bytes_units[-1]
            c = c / 1024
        return (str(c) if (i == 0) else '{:.2f}'.format(c)) + cls.bytes_units[i]

    # 日期单位 ['秒', '分', '时', '天', '周', '月', '年', '世纪']
    date_units = ['s', 'm', 'h', 'd', 'w', 'M', 'y', 'c']

    @classmethod
    def readable_seconds(cls, s):
        """ 对秒的整理, 整理至分或时或天等 """

        # 单位下标
        i = 0

        for _ in cls.date_units[1:]:
            # 整理分时
            if i in [1, 2] and s > 60:
                s = s / 60
            elif i == 3 and s > 24:
                s = s / 24
            elif i == 4 and s > 7:
                s = s / 7
            elif i == 5 and s > 4:
                s = s * 7 / 30
            elif i == 6 and s > 12:
                s = s * 30 / 365
            elif i == 7 and s > 100:
                s = s / 100
            else:
                break
            i += 1

        return ('>99' + cls.date_units[-1]) if s > 100 and i == (len(cls.date_units) - 1) else (str(int(s)) + cls.date_units[i])


class ProgressBarOptions:
    """ 进度条配置 """

    # 上传进度条字符
    char = '='
    # 上传进度条剩余内容的字符
    empty_char = ' '
    # 字符数量
    count = 50

