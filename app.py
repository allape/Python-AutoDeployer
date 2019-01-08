# @author AllenSnape
# @email allensnape@gmail.com

import os
import sys
import time
import warnings
import threading

import paramiko
import xml.etree.ElementTree as ET

import progress_bar.ProgressBar as PB

# region 软件配置

display_path_length = 57  # 显示路径的长度, 用于美化输出的
display_path_prefix_dot = '.'  # 显示多余内容的符号
display_path_prefix_count = 3  # 显示多余内容的符号数量

progress_bar_char = '='  # 上传进度条字符
progress_bar_empty_char = ' '  # 上传进度条剩余内容的字符
progress_bar_count = 50  # 字符数量

# endregion

# region 软件默认值

default_port = 22
default_username = 'root'
default_password = None
default_charset = 'utf8'
default_fs_sep = '/'


# endregion


def exec_commands(commands, hostname, port=default_port, username=default_username, password=default_password,
                  charset=default_charset):
    """ 执行shell """

    if commands is None or len(commands) == 0:
        return

    # 初始化ssh客户端
    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connection.connect(hostname, port, username, password)

    # 获取交互式shell
    chan = connection.invoke_shell()

    # 执行命令
    for c in commands:
        # 发送命令
        chan.send(c + '\n')

        # 等待
        time.sleep(0.5)

        # 输出
        while True:
            # 获取终端内容
            res = chan.recv(65535).decode(charset)
            # 输出内容
            sys.stdout.write(res)
            sys.stdout.flush()

            # 退出死循环
            if res.endswith('# ') or res.endswith('$ '):
                break

    # 关闭连接
    connection.close()


def upload(source, target, hostname, port=default_port, username=default_username, password=default_password,
           fs_sep=default_fs_sep):
    """ 上传文件 """

    # 初始化sftp
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # 实际的发送文件
    def put(p, d):
        """ 实际的发送文件 """
        # 创建文件夹
        new_d = fs_sep if d[0] == fs_sep else ''
        for folder in d[:d.rfind(fs_sep)].split(fs_sep):
            new_d += fs_sep + folder
            try:
                sftp.stat(new_d)
            except:
                sftp.mkdir(new_d)

        # 打印开始
        pdppc = display_path_prefix_count if len(p) - display_path_length > 3 else (len(p) - display_path_length)
        ddppc = display_path_prefix_count if len(d) - display_path_length > 3 else (len(d) - display_path_length)
        print(
            (
                p.ljust(display_path_length) if len(p) < display_path_length else
                (display_path_prefix_dot * pdppc + p[len(p) - display_path_length + pdppc:])
            ) + ' -> ' +
            (
                d.ljust(display_path_length) if len(d) < display_path_length else
                (display_path_prefix_dot * ddppc + d[len(d) - display_path_length + ddppc:])
            )
        )

        # 进度条配置
        pbo = PB.ProgressBarOptions()
        pbo.char = progress_bar_char
        pbo.count = progress_bar_count
        pbo.empty_char = progress_bar_empty_char

        # 实例化进度条
        pb = PB.ProgressBar(pbo)

        # 上传文件
        sftp.put(p, d, pb.update)

        # 美化输出
        print('\n')

    # 判断是否是文件夹
    if os.path.isdir(source):
        def put_dir(p, folders=None):
            # 整理格式
            if folders is None:
                folders = []

            # 循环目录
            new_p = (p if p[len(p) - 1] == os.path.sep else (p + os.path.sep)) + (
                os.path.sep.join(folders) + os.path.sep if len(folders) > 0 else '')
            for f in os.listdir(new_p):
                local_folder = new_p + f
                if os.path.isdir(local_folder):
                    new_folders = folders.copy()
                    new_folders.append(f)
                    put_dir(p, new_folders)
                else:
                    put(local_folder, (target if target[-1:] == fs_sep else (target + fs_sep)) + (
                        fs_sep.join(folders) + fs_sep if len(folders) > 0 else '') + f)

        put_dir(source)
    # 不是文件夹则直接上传, 判断一次保存路径是否是/结尾, 如果是, 则使用提供的源文件的名称
    else:
        put(source, target + source[source.rfind(os.path.sep) + 1:] if target[-1:] == fs_sep else target)

    # 关闭连接
    transport.close()


def exec_local_commands(commands):
    """ 执行本地脚本 """
    for c in commands:
        print('>', c)
        if os.system(c) != 0:
            raise Exception('本地脚本执行出错:', c)


def read_config(config_file):
    # 读取xml文件
    tree = ET.parse(config_file)
    # 获取根节点
    root = tree.getroot()

    def read_commands(xml, obj, key):
        """ 读取命令字段 """
        if xml.find(key) is not None:
            obj[key] = []
            for c in xml.find(key).findall('command'):
                obj[key].append(rp(properties, c.text))

    # 读取资源
    properties = []
    if root.find('properties') is not None:
        for pro in root.find('properties').iter():
            properties.append({'label': pro.tag, 'value': pro.text})

    # 读取本地配置(可以不存在, 那么此时只需要执行远程服务器命令即可, 先执行before, 后执行after)
    local = {}
    # local_xml
    lx = root.find('local')
    if lx is None:
        warnings.warn('config.local配置不存在, 将会直接执行服务器命令!')
    else:
        # 上传的文件或文件夹
        local['source'] = rp(properties, lx.find('source').text) if lx.find('source') is not None else None
        local['fs_sep'] = rp(properties, lx.find('fs_sep').text) if lx.find('fs_sep') is not None else None
        # 上传前执行的命令
        read_commands(lx, local, 'before')
        # 上传后执行的命令
        read_commands(lx, local, 'after')

    # 读取远程配置
    remote = {}
    # remote_xml
    rl = root.find('remote')
    if rl is None:
        raise Exception('远程配置(config.remote)不得为空!')
    # servers_xml
    ssl = rl.find('servers')
    if ssl is None:
        raise Exception('远程配置(config.remote.servers)不得为空!')
    # servers_server_xml
    sssl = ssl.findall('server')
    if len(sssl) == 0:
        raise Exception('远程配置(config.remote.servers.server)必须至少存在一条!')
    # 读取服务器配置
    remote['servers'] = []
    # server_xml
    for sl in sssl:
        server = {'host': rp(properties, sl.find('host').text) if sl.find('host') is not None else None}
        if server['host'] is None:
            warnings.warn('host不得为空!')
            continue
        server['target'] = rp(properties, sl.find('target').text) if sl.find('target') is not None else None
        if server['target'] is None:
            warnings.warn('target不得为空!')
            continue
        server['port'] = rp(properties, sl.find('port').text) if sl.find('port') is not None else None
        server['username'] = rp(properties, sl.find('username').text) if sl.find('username') is not None else None
        server['password'] = rp(properties, sl.find('password').text) if sl.find('password') is not None else None
        server['charset'] = rp(properties, sl.find('charset').text) if sl.find('charset') is not None else None
        server['fs_sep'] = rp(properties, sl.find('fs_sep').text) if sl.find('fs_sep') is not None else None
        read_commands(sl, server, 'before')
        read_commands(sl, server, 'after')

        remote['servers'].append(server)

    if len(remote['servers']) == 0:
        raise Exception('无远程命令可执行!')

    # print(local)
    # print(remote)
    # return

    # 开始执行
    # 执行本地命令
    if 'before' in local and local['before'] is not None and len(local['before']) > 0:
        print('开始执行本地上传前命令')
        exec_local_commands(local['before'])
        print()

    for server in remote['servers']:
        if 'before' in server and server['before'] is not None and len(server['before']) > 0:
            print('开始执行[' + server['host'] + ']上传前命令', end='\n\n')
            exec_commands(server['before'], server['host'],
                          int(server['port'] if server['port'] is not None else default_port),
                          server['username'] if server['username'] is not None else default_username,
                          server['password'] if server['password'] is not None else default_password,
                          server['charset'] if server['charset'] is not None else default_charset)

        # 如果存在上传的文件或文件夹, 则进行上传
        print('\n')
        if 'source' in local and local['source'] is not None:
            print('\n开始上传\n')
            upload(local['source'], server['target'], server['host'],
                   int(server['port'] if server['port'] is not None else default_port),
                   server['username'] if server['username'] is not None else default_username,
                   server['password'] if server['password'] is not None else default_password,
                   server['fs_sep'] if server['fs_sep'] is not None else default_fs_sep)

        if 'after' in server and server['after'] is not None and len(server['after']) > 0:
            print('开始执行[' + server['host'] + ']上传后命令', end='\n\n')
            exec_commands(server['after'], server['host'],
                          int(server['port'] if server['port'] is not None else default_port),
                          server['username'] if server['username'] is not None else default_username,
                          server['password'] if server['password'] is not None else default_password,
                          server['charset'] if server['charset'] is not None else default_charset)

    # 执行本地命令
    if 'after' in local and local['after'] is not None and len(local['after']) > 0:
        print('\n\n开始执行本地上传后命令', end='\n')
        exec_local_commands(local['after'])
        print()


def rp(properties, source):
    """ replace_properties: 替换资源数据 """
    if source is not None and isinstance(source, str):
        for pro in properties:
            source = source.replace('${' + pro['label'] + '}', pro['value'])
        return source
    return source


if __name__ == '__main__':
    # 配置文件集合
    configs = []

    # 是否以异步方式执行
    run_in_asynchronized = False

    for arg in sys.argv[1:]:
        if arg == '--async':
            run_in_asynchronized = True
        else:
            if os.path.exists(arg):
                configs.append(arg)
            else:
                warnings.warn(f'文件{arg}不存在!')

    # 读取参数
    if len(configs) == 0:
        raise Exception('请输入配置文件路径!')

    threads = []

    for c in configs:
        if run_in_asynchronized:
            ac = threading.Thread(target=read_config, args=(c, ))
            ac.start()
            threads.append(ac)
        else:
            read_config(c)

    for t in threads:
        t.join()
