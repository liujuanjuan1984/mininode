# quorum-mininode-python

a mini python sdk for quorum lightnode with http/https requests to quorum fullnode

这是 quorum lightnode（轻节点）的 python sdk 实现之一。

另外一个实现为 zhangwm404 的 [quorum-lightnode-py](https://github.com/zhangwm404/quorum-lightnode-py)。

特点是：聚焦单个种子网络，实现 http/https 请求，封装 lightnode 相关 api 与常见的方法；同时不做任何本地数据存储，把存储部分交给 bot/app/web 的开发者自行拓展。

### 安装

```sh
pip install mininode
```

参考案例 [example](./example/)

## 参与代码贡献

### 依赖：

```sh
pipenv install
pipenv run python example/send_to_group.py
```


代码格式化：

```sh
isort .
black -l 120 -t py39 .
```

代码检查：

```sh
pylint mininode
```