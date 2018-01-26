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


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////


day-3
	创建orm.py文件

day-4
	创建models.py文件
	把Web App需要的3个表用Model表示出来：

day-5
	创建coroweb.py文件(编写Web框架)
	在正式开始Web开发前，我们需要编写一个Web框架。
	#最后，在app.py中加入middleware、jinja2模板和自注册的支持：

	aiohttp已经是一个Web框架了，为什么我们还需要自己封装一个？
	原因是从使用者的角度来说，aiohttp相对比较底层，编写一个URL的处理函数需要这么几步：
	第一步，编写一个用@asyncio.coroutine装饰的函数：
	@asyncio.coroutine
	def handle_url_xxx(request):
	    pass
	第二步，传入的参数需要自己从request中获取：
	url_param = request.match_info['key']
	query_params = parse_qs(request.query_string)
	最后，需要自己构造Response对象：

	text = render('template', data)
	return web.Response(text.encode('utf-8'))
	这些重复的工作可以由框架完成。例如，处理带参数的URL/blog/{id}可以这么写：

	@get('/blog/{id}')
	def get_blog(id):
	    pass
	处理query_string参数可以通过关键字参数**kw或者命名关键字参数接收：

	@get('/api/comments')
	def api_comments(*, page='1'):
	    pass
	对于函数的返回值，不一定是web.Response对象，可以是str、bytes或dict。

	如果希望渲染模板，我们可以这么返回一个dict：

	return {
	    '__template__': 'index.html',
	    'data': '...'
	}
	因此，Web框架的设计是完全从使用者出发，目的是让使用者编写尽可能少的代码。

	编写简单的函数而非引入request和web.Response还有一个额外的好处，就是可以单独测试，否则，需要模拟一个request才能测试。



day-6

	创建config_default.py文件(编写配置文件)
	把config_default.py作为开发环境的标准配置，把config_override.py作为生产环境的标准配置，我们就可以既方便地在本地开发，又可以随时把应用部署到服务器上。
	应用程序读取配置文件需要优先从config_override.py读取。为了简化读取配置文件，可以把所有配置读取到统一的config.py中

	有了Web框架和ORM框架，我们就可以开始装配App了。
	通常，一个Web App在运行时都需要读取配置文件，比如数据库的用户名、口令等，在不同的环境中运行时，Web App可以通过读取不同的配置文件来获得正确的配置。

	由于Python本身语法简单，完全可以直接用Python源代码来实现配置，而不需要再解析一个单独的.properties或者.yaml等配置文件。

	默认的配置文件应该完全符合本地开发环境，这样，无需任何设置，就可以立刻启动服务器。


day-7
	编写MVC，根目录templates下创建test.html
	day-7中初次定义index函数

	现在，ORM框架、Web框架和配置都已就绪，我们可以开始编写一个最简单的MVC，把它们全部启动起来。
	通过Web框架的@get和ORM框架的Model支持，可以很容易地编写一个处理首页URL的函数


day-8
	构建前端，创建父模板__base__.html;从__base__.html继承一个blogs.html;并重新定义handlers文件中的index方法;最后在app.py文件中创建时间过滤器datetime_filter

	虽然我们跑通了一个最简单的MVC，但是页面效果肯定不会让人满意。

	对于复杂的HTML前端页面来说，我们需要一套基础的CSS框架来完成页面布局和基本样式。另外，jQuery作为操作DOM的JavaScript库也必不可少。

	从零开始写CSS不如直接从一个已有的功能完善的CSS框架开始。有很多CSS框架可供选择。我们这次选择uikit这个强大的CSS框架。它具备完善的响应式布局，漂亮的UI，以及丰富的HTML组件，让我们能轻松设计出美观而简洁的页面。

	可以从uikit首页下载打包的资源文件。
	所有的静态资源文件我们统一放到www/static目录下

	Blog的创建日期显示的是一个浮点数，因为它是由这段模板渲染出来的：
	<p class="uk-article-meta">发表于{{ blog.created_at }}</p>
	解决方法是通过jinja2的filter（过滤器），把一个浮点数转换成日期字符串。我们来编写一个datetime的filter，在模板里用法如下：
	<p class="uk-article-meta">发表于{{ blog.created_at|datetime }}</p>
	filter需要在初始化jinja2时设置。相关代码如下：

day-9
	编写API,在handlers中定义API,并创建apis.py文件。
	
	由于API就是把WebApp的功能全部封装，所以，通过API操作数据，可以极大地把前端和后端的代码隔离，使得后端代码易于测试，前端代码编写更简单
	一个API也是一个URL的处理函数，我们希望能直接通过一个@api来把函数变成JSON格式的REST API，

	我们需要对Error进行处理，因此定义一个APIError，这种Error是指API调用时发生了逻辑错误（比如用户不存在），其他的Error视为Bug，返回的错误代码为internalerror。


day-10
	用户注册和登录,编写注册函数、登录api和注册页面register.html;并在app.py中编写auth_factory过滤器



day-11
	 编写日志创建页,选择Vue这个简单易用的MVVM框架来实现创建Blog的页面templates/manage_blog_edit.html,并在handlers中增加函数

	需要特别注意的是，在MVVM中，Model和View是双向绑定的。如果我们在Form中修改了文本框的值，可以在Model中立刻拿到新的值。试试在表单中输入文本，然后在Chrome浏览器中打开JavaScript控制台，可以通过vm.name访问单个属性，或者通过vm.$data访问整个Model：

	双向绑定是MVVM框架最大的作用。借助于MVVM，我们把复杂的显示逻辑交给框架完成。由于后端编写了独立的REST API，所以，前端用AJAX提交表单非常容易，前后端分离得非常彻底。


day-12
	编写日志列表页,在apis.py中定义一个Page类用于存储分页信息,创建manage_blogs.html,在handlers.py中实现API：,创建manage_blogs.html



day-13
	提升开发效率,创建pymonitor.py文件

	注意到每次修改Python代码，都必须在命令行先Ctrl-C停止服务器，再重启，改动才能生效。
	服务器检测到代码修改后自动重新加载,Django的开发环境在Debug模式下就可以做到自动重新加载，如果我们编写的服务器也能实现这个功能，就能大大提升开发效率。

	其实Python本身提供了重新载入模块的功能，但不是所有模块都能被重新载入。另一种思路是检测www目录下的代码改动，一旦有改动，就自动重启服务器。

	按照这个思路，我们可以编写一个辅助程序pymonitor.py，让它启动wsgiapp.py，并时刻监控www目录下的代码改动，有改动时，先把当前wsgiapp.py进程杀掉，再重启，就完成了服务器进程的自动重启。

	要监控目录文件的变化，我们也无需自己手动定时扫描，Python的第三方库watchdog可以利用操作系统的API来监控目录文件的变化，并发送通知。我们先用pip安装：


day-14
	完成Web App,添加后端api ;创建blog.html,manage_comments.html,manage_users.html

	在Web App框架和基本流程跑通后，剩下的工作全部是体力活了：在Debug开发模式下完成后端所有API、前端所有页面。我们需要做的事情包括：

	把当前用户绑定到request上，并对URL/manage/进行拦截，检查当前用户是否是管理员身份：


day-15
	部署Web App,把awesome-python3-webapp部署到Linux服务器。

	搭建Linux服务器

	部署方式
		利用Python自带的asyncio，我们已经编写了一个异步高性能服务器。但是，我们还需要一个高性能的Web服务器，这里选择Nginx，它可以处理静态资源，同时作为反向代理把动态请求交给Python代码处理。

		在服务器端，我们需要定义好部署的目录结构：
		/
		+- srv/
		   +- awesome/       <-- Web App根目录
		      +- www/        <-- 存放Python源码
		      |  +- static/  <-- 存放静态资源文件
		      +- log/        <-- 存放log
		在服务器上部署，要考虑到新版本如果运行不正常，需要回退到旧版本时怎么办。每次用新的代码覆盖掉旧的文件是不行的，需要一个类似版本控制的机制。由于Linux系统提供了软链接功能，所以，我们把www作为一个软链接，它指向哪个目录，哪个目录就是当前运行的版本：  
		
		在服务器上部署，要考虑到新版本如果运行不正常，需要回退到旧版本时怎么办。每次用新的代码覆盖掉旧的文件是不行的，需要一个类似版本控制的机制。由于Linux系统提供了软链接功能，所以，我们把www作为一个软链接，它指向哪个目录，哪个目录就是当前运行的版本： 


		Nginx可以作为服务进程直接启动，但app.py还不行，所以，Supervisor登场！Supervisor是一个管理进程的工具，可以随系统启动而启动服务，它还时刻监控服务进程，如果服务进程意外退出，Supervisor可以自动重启服务。   

