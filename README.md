# Python-AutoDeployer

python3 自动部署脚本

## 安装教程 / Installation

``` shell
    git clone https://github.com/allensnape/Python-AutoDeployer
    cd Python-AutoDeployer
    # python -m pip install -r requirements.txt
    pip3 install -r requirements.txt
```

## 配置说明 / Configuration
见config.xml和config.xsd / See config.xml and config.xsd

## 使用方式 / Usage

``` shell
    # 在配置好config.xml后 / After config.xml is setted
    python ./app.py config.xml
    # 也可以执行多个配置文件, 先进先出 / Multi-deployment within FIFO
    #python ./app.py config.0.xml config.1.xml
    # 使用多个配置文件时可以开启异步执行(log会交叉输出) / You can deploy projects asynchronized in multi-deployment (warning: log in terminal will be mixed up)
    #python ./app.py config.0.xml config.1.xml --async
```
