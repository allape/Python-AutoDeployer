# py-auto-deploy

python3 自动部署脚本

## 安装教程

1. pip3 install -r requirement.txt

## 使用方式

``` shell
    git clone https://gitee.com/AllenSnape/py-auto-deploy.git
    cd py-auto-deploy
    # 在配置好config.xml后
    python app.py config.xml
    # 也可以执行多个配置文件, 同步执行, 先进先出
    #python ./app.py config.0.xml config.1.xml
```

## 配置说明
见config.xml和config.xsd