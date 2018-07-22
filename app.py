import sys, os, json, time, traceback

import paramiko

class ProgressBar:
    ''' 进度条 '''

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
        self.options.char = ProgressBarOptions.char if (self.options.char is None or len(self.options.char) == 0) else self.options.char[0]
        self.options.empty_char = ProgressBarOptions.empty_char if (self.options.empty_char is None or len(self.options.empty_char) == 0) else self.options.empty_char[0]
        self.options.count = ProgressBarOptions.count if (self.options.count is None or isinstance(self.options.count, int) is not True or self.options.count <= 0) else self.options.count


        # 初始化数据
        self.transferred_log = {}       # 上传记录; k: 上传时间, v: 上传的bytes
        self.last_transferred = 0       # 上次上传了的字节数量
        self.update_count = 0           # 更细进度条的次数

        # 输出占位符
        print(' ' * (self.options.count + self.other_length), end = '')

    def update(self, transferred, total):
        ''' 更新进度条 '''

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
                (self.readable_bytes(transferred_in_last_second).rjust(10, ' ') + '/s') + \
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
        ''' 整理字节长度, 优化人类阅读 '''

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
        ''' 对秒的整理, 整理至分或时或天等 '''

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
    ''' 进度条配置 '''

    # 上传进度条字符
    char = '='
    # 上传进度条剩余内容的字符
    empty_char = ' '
    # 字符数量
    count = 50

# region 软件配置

display_path_length = 57        # 显示路径的长度, 用于美化输出的
display_path_prefix_dot = '.'   # 显示多余内容的符号
display_path_prefix_count = 3   # 显示多余内容的符号数量

progress_bar_char = '='                     # 上传进度条字符
progress_bar_empty_char = ' '               # 上传进度条剩余内容的字符
progress_bar_count = 50                     # 字符数量

# endregion

# region SSH连接信息
hostname = ''
port = 22
username = 'root'
password = ''
charcode = 'utf8'
# endregion

# region 远程配置数据

remote_fs_sep = '/'             # 远程服务器文件系统路径分隔符
remote_deploy_path = '/test/'   # 远程服务器部署目录
remote_before_upload = []       # 上传之前连接服务器执行的shell脚本; 可包含元素: 1/ 脚本命令. 2/ {"commands": ["脚本命令"], "vars": {"k": "v"}}. 脚本命令可以包含花括号(是为了引用全局变量, 栗子: "cd {remote_deploy_path}"; 为字典时, vars里面的元素也会update到全局变量的字典中)
remote_after_uploaded = []      # 上传之后执行的shell脚本

# endregion

# region 本地配置数据

local_source_path = './'                # 项目路径
local_before_upload = []                # 上传之前执行的本地脚本
local_after_uploaded = []               # 上传之后执行的本地脚本

# endregion

# region 读取配置有效的字段与转换

config_available_keys = {
    'remote': {
        # 连接地址
        'hostname': 'hostname',
        # 端口号
        'port':     'port',
        # 账号
        'username': 'username',
        # 密码
        'password': 'password',
        # 编码
        'charcode': 'charcode',

        # 服务器文件系统分隔符
        'fs_sep':           'remote_fs_sep',
        # 部署路径
        'deploy_path':      'remote_deploy_path',
        # 上传之前执行的shell
        'before_upload':    'remote_before_upload',
        # 上传之后执行的shell
        'after_uploaded':   'remote_after_uploaded'
    },
    'local': {
        # 上传的目录
        'source_path':      'local_source_path',

        # 上传之前执行的本地脚本
        'before_upload':    'local_before_upload',
        # 上传之后执行的本地脚本
        'after_uploaded':   'local_after_uploaded'
    },
    # 软件配置
    'config': {
        # 显示路径的长度, 用于美化输出的
        'display_path_length': 'display_path_length',
        # 上传进度条字符
        'progress_bar_char': 'progress_bar_char',
        # 上传进度条剩余内容的字符
        'progress_bar_empty_char': 'progress_bar_empty_char',
        # 字符数量
        'progress_bar_count': 'progress_bar_count',
    }
}

# endregion

def exec_commands(commands = []):
    ''' 执行sh '''

    if len(commands) == 0:
        return

    # 初始化ssh客户端
    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connection.connect(hostname, port, username, password)

    # 获取交互式shell
    chan = connection.invoke_shell()

    # 执行命令
    for c in commands:
        try:
            # 发送命令
            chan.send(c + '\n')

            # 等待 FIXME 执行后获取内容有延迟
            time.sleep(0.5)

            # 输出
            while True:
                # 获取终端内容
                res = chan.recv(65535).decode(charcode)
                # 输出内容
                sys.stdout.write(res)
                sys.stdout.flush()

                # 退出死循环
                if res.endswith('# ') or res.endswith('$ '):
                    break
        except: 
            print('Exection Err:\n', traceback.format_exc())

    # 关闭连接
    connection.close()

def upload(path, dest = remote_fs_sep):
    ''' 上传文件 '''

    # 初始化sftp
    transport = paramiko.Transport((hostname, port))
    transport.connect(username = username, password = password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # 实际的发送文件
    def put(p, d):
        ''' 实际的发送文件 '''
        # 创建文件夹
        new_d = remote_fs_sep if d[0] == remote_fs_sep else ''
        for folder in d[:d.rfind(remote_fs_sep)].split(remote_fs_sep):
            new_d += remote_fs_sep + folder
            try:
                sftp.stat(new_d)
            except:
                sftp.mkdir(new_d)

        # 打印开始
        pdppc = display_path_prefix_count if len(p) - display_path_length > 3 else (len(p) - display_path_length)
        ddppc = display_path_prefix_count if len(d) - display_path_length > 3 else (len(d) - display_path_length)
        print( \
            ( \
                p.ljust(display_path_length) if len(p) < display_path_length else \
                (display_path_prefix_dot * pdppc + p[len(p) - display_path_length + pdppc:]) \
            ) + ' -> ' + \
            ( \
                d.ljust(display_path_length) if len(d) < display_path_length else \
                (display_path_prefix_dot * ddppc + d[len(d) - display_path_length + ddppc:]) \
            ) \
        )

        # 进度条配置
        pbo = ProgressBarOptions()
        pbo.char = progress_bar_char
        pbo.count = progress_bar_count
        pbo.empty_char = progress_bar_empty_char

        # 实例化进度条
        pb = ProgressBar(pbo)

        # 上传文件
        sftp.put(p, d, pb.update)

        # 美化输出
        print('\n')

    # 判断是否是文件夹
    if os.path.isdir(path):
        def put_dir(p, folders = None):
            # 整理格式
            if folders is None:
                folders = []

            # 循环目录
            new_p = (p if p[len(p) - 1] == os.path.sep else (p + os.path.sep)) + (os.path.sep.join(folders) + os.path.sep if len(folders) > 0 else '')
            for f in os.listdir(new_p):
                local_folder = new_p + f
                if os.path.isdir(local_folder):
                    new_folders = folders.copy()
                    new_folders.append(f)
                    put_dir(p, new_folders)
                else:
                    put(local_folder, (dest if dest[-1:] == remote_fs_sep else (dest + remote_fs_sep)) + (remote_fs_sep.join(folders) + remote_fs_sep if len(folders) > 0 else '') + f)
        put_dir(path)
    # 不是文件夹则直接上传, 判断一次保存路径是否是/结尾, 如果是, 则使用提供的源文件的名称
    else:
        put(path, dest + path[path.rfind(os.path.sep) + 1:] if dest[-1:] == remote_fs_sep else dest)
        
    # 关闭连接
    transport.close()

def format_commands(commands):
    ''' 格式化命令 '''

    # 格式化之后的命令数组
    formatted_commands = []

    # 循环整理
    for c in commands:
        # 初始化数据
        command, formats = c, globals().copy()

        # 如果是字典类型, 则表示是需要配置的命令
        if isinstance(c, dict):
            # 合并全局变量和配置的变量
            formats.update(c['vars'] if 'vars' in c else {})
            # 获取需要特殊处理的命令
            sub_commands = c['commands']
            # 循环整理
            for sc in sub_commands:
                # 整理后放入数组
                formatted_commands.append(sc.format(**formats))
        else:
            # 是字符串就直接进行整理
            formatted_commands.append(command.format(**formats))
    return formatted_commands

def exec_local_commands(commands):
    ''' 执行本地脚本 '''
    for c in commands:
        if os.system(c) != 0:
            raise Exception('本地脚本执行出错:', c)

def read_config(config_file):
    ''' 读取配置信息 '''
    try:
        # 判断文件是否存在
        if os.path.isfile(config_file):
            # 打开配置文件
            with open(config_file, 'r', encoding = charcode) as f:
                # 读取配置文件为JSOn
                configs = json.load(f)
                # 循环设置本地字段
                for m in configs:
                    for mk in configs[m]:
                        # print(config_available_keys[m][mk], ':', configs[m][mk])
                        globals()[config_available_keys[m][mk]] = configs[m][mk]

                # 整理参数
                global display_path_length
                display_path_length = 50 if (display_path_length is None or isinstance(display_path_length, int) is not True or display_path_length < 3) else display_path_length
                
                # 开始执行上传之前的本地脚本
                exec_local_commands(format_commands(local_before_upload))
                # 开始执行上传之前的远程脚本
                print()
                exec_commands(format_commands(remote_before_upload))
                print('\n\n')

                # 开始上传
                upload(local_source_path, remote_deploy_path)

                # 开始执行上传之后的远程脚本
                print()
                exec_commands(format_commands(remote_after_uploaded))
                # 开始执行上传之后的本地脚本
                print()
                exec_local_commands(format_commands(local_after_uploaded))
                print()

        else:
            raise Exception('配置文件不存在: ', config_file)
    except:
        print('部署失败:\n', traceback.format_exc())
        
if __name__ == '__main__':

    # 清空控制台
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

    # 读取参数
    if len(sys.argv) == 1:
        raise Exception('请输入配置文件路径')

    for arg in sys.argv[1:]:
        read_config(arg)
