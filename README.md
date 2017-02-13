# awesome-python3-webapp
learning python3

目标：实战目标是一个Blog网站，包含日志、用户和评论3大部分。

搭建开发环境

首先，确认系统安装的Python版本是3.5.x：
$ python3 --version
Python 3.5.1

然后，用pip安装开发Web App需要的第三方库：

异步框架aiohttp：
$pip3 install aiohttp

前端模板引擎jinja2：
$ pip3 install jinja2

MySQL 5.x数据库，从官方网站下载并安装，安装完毕后，请务必牢记root口令。为避免遗忘口令，建议直接把root口令设置为password；

MySQL的Python异步驱动程序aiomysql：
$ pip3 install aiomysql

