# py-auto-deploy

python3 自动部署脚本

## 安装教程

1. pip3 install -r requirement.txt

## 使用方式

``` shell
    git clone https://gitee.com/AllenSnape/py-auto-deploy.git
    cd py-auto-deploy
    # 同步执行, 谁在前面谁先玩完儿
    python app.py 配置文件1.json 配置文件2.json ...
```

## 配置说明

> config.json
>> 1. remote: 服务端配置 
>>> 1. hostname: SSH地址
>>> 2. port:     SSH端口
>>> 3. username: SSH登录账号
>>> 4. password: SSH登录密码
>>> 5. charcode: 传输时的编码格式
>>> 6. fs_sep:  服务器文件系统分隔符
>>> 7. deploy_path: 部署文件/目录; 多层目录时会自动创建
>>> 8. before_upload: 上传之前执行的远程sh命令, 多条命令同属一个session. *注解1
>>> 9. after_uploaded: 上传之后执行的远程sh命令, 多条命令同属一个session. *注解1
>> 2. local:  本地配置
>>> 1. source_path: 上传的文件/目录
>>> 2. before_upload: 上传之前执行的本地命令. *注解1
>>> 3. after_uploaded: 上传之后执行的本地命令. *注解1
>> 3. config: 软件配置
>>> 1. display_path_length: 显示路径的长度, 用于美化输出的; 仅限正整数且大于3
>>> 2. progress_bar_char: 上传进度条字符; 单个字符, 多个字符时仅截取第一个
>>> 3. progress_bar_empty_char: 上传进度条剩余内容的字符; 单个字符, 多个字符时仅截取第一个
>>> 4. progress_bar_count: 字符数量; 仅限正整数

### 注解1

``` python

    # before_upload和after_uploaded是一个集合, 元素可为字符串或一个对象

    # 当为字符串时, 就是一条命令行

    # 当为一个{commands: ['', ...], vars: {k: v, ...}的字典时(为字典时必须包含这两个成员):
    # commands是命令模板, vars为填充的字典(会和全局变量合并, 如果提供的键和全局变量名重名则会优先使用提供的)
    # 发送命令前会做如下处理
    vars.update(globals())
    for c in commands:
        c = c.format(**vars)
    # 有效的全局变量名有...app.py代码前半部分声明的变量

    # 栗子一号: 在上传之前删除服务器部署目录下的内容
        {
            "remote": {
                ...
                "deploy_path": "/var/www/",
                "before_upload": ["rm -rf {remote_deploy_path}*"],
                ...
            },
            ...
        }

    # 栗子二号: 更新本地代码, 编译项目后上传至服务器, 上传完成后再开启docker
        {
            "remote": {
                ...
                "deploy_path": "/usr/bin/local/xxx/",
                "before_upload": ["rm -f {remote_deploy_path}xxx.jar"],
                "after_uploaded": [
                    "pwd",
                    {
                        "vars": {
                            "path": "/home/projects/xxx/"
                        },
                        "commands": [
                            "cd {path}",
                            "docker-compose stop",
                            "docker build -t xxx.jar .",
                            "docker-compose up -d"
                        ]
                    }
                ]
            },
            "local": {
                "source_path": "/root/projects/xxx/xxx.jar",
                "before_upload": [
                    "cd /root/projects/xxx && git pull origin master && mvn clean compile"
                ]
                ...
            }
        }
```
