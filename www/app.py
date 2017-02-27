#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = ''

#logging模块定义了一些函数和模块，可以帮助我们对一个应用程序或库实现一个灵活的事件日志处理系统;logging模块支持将日志信息保存到不同的目标域中
#logging.basicConfig(filename = os.path.join(os.getcwd(), 'log.txt'), level = logging.DEBUG)   将会在程序的根目录下创建一个log.txt文件
# 日志级别大小关系为：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
#默认情况下，logging将日志打印到屏幕，日志级别为WARNING；
import logging; logging.basicConfig(level=logging.INFO)        #在调用logging.basicConfig前不能调用logging的相关函数，否则会导致设置失效，系统使用默认的日志文件

# asyncio 内置了对异步IO的支持;os模块提供了调用操作系统的接口函数;json模块提供了Python对象到Json模块的转换;time模块提供各种操作时间的函数
import asyncio,os,json,time
# datetime是处理日期和时间的标准库
from datetime import datetime

# aiohttp是基于asyncio实现的http框架
from aiohttp import web

def index(request):
	#如果不指定content_type='text/html',用浏览器打开会弹出下载框
	return web.Response(body=b'<h1>Awesome</h1>', content_type='text/html', charset='UTF-8')
	
#注意aiohttp的初始化函数init()也是一个coroutine，loop.create_server()则利用asyncio创建TCP服务	
# 调用asyncio实现异步IO
@asyncio.coroutine
def init(loop):
	app = web.Application(loop=loop)

	app.router.add_route('GET','/',index)
	srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9009)
	logging.info('server started at http://127.0.0.1:9000...')
	return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
	
