# 路径
* 代码在42.137路径： **/opt/liziran/email_abstraction/**
* 代码在创建软链和同步写入代码前，需要对该目录进行赋权：**sudo chmod -R 777 /opt/liziran/email_abstraction/**

# 环境安装
```shell
conda create -n liziran python=3.10.12

conda activate liziran

pip install -r requirements.txt
```

# 执行顺序
```shell
sh ops.sh start
```