# 安装
```shell
conda create -n liziran python=3.10.12

conda activate liziran

pip install -r requirements.txt
```

# 执行顺序
```shell
conda activate liziran

export http_proxy=http://10.0.0.5:3128; export https_proxy=http://10.0.0.5:3128

python 
```