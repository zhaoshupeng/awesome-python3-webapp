#有了ORM，我们就可以把Web App需要的3个表用Model表示出来：
#uuid是python中生成唯一ID的库
import time,uuid

from orm import Model,StringField,BooleanField,FloatField,TextField

# 这个函数的作用是生成一个基于时间的独一无二的id，来作为数据库表中每一行的主键
def next_id():
	# time.time() 返回当前时间的时间戳(相对于1970.1.1 00:00:00以秒计算的偏移量)
    # uuid4()——由伪随机数得到，有一定的重复概率，该概率可以计算出来。
	return '%015d%s000' % (int(time.time() * 1000),uuid.uuid4().hex)

# 这是一个用户名的表
class User(Model):
	__table__ = "users"

	#在编写ORM时，给一个Field增加一个default参数可以让ORM自己填入缺省值，非常方便。并且，缺省值可以作为函数对象传入，在调
	#用save()时自动计算(需自己验证)。例如，主键id的缺省值是函数next_id，创建时间created_at的缺省值是函数time.time，可以自动设
	#置当前日期和时间。
	id = StringField(primary_key=True, default=next_id(), ddl="varchar(50)")
	#id = StringField(primary_key=True, default=next_id(), ddl="varchar(50)")
	email = StringField(ddl="varchar(50)")
	passwd = StringField(ddl="varchar(50)")
	admin = BooleanField()  # 管理员，True表示该用户是管理员，否则不是
	name = StringField(ddl="varchar(50)")
	image = StringField(ddl="varchar(500)")  # 头像
	created_at = FloatField(default=time.time)  # 创建时间默认是为当前时间

# 这是一个博客的表
class Blog(Model):
	__table__ = "blogs"

	id = StringField(primary_key=True, default=next_id())
	user_id = StringField(ddl="varchar(50)")  # 作者id
	user_name = StringField(ddl="varchar(50)")  # 作者名
	user_image = StringField(ddl="varchar(500)")  # 作者上传的图片
	name = StringField(ddl="varchar(50)")  # 文章名
	summary = StringField(ddl="varchar(200)")  # 文章概要
	content = TextField()  # 文章正文
	created_at = FloatField(default=time.time)


# 这是一个评论的表
class Comment(Model):
	__table__ = "comments"
	id = StringField(primary_key=True, default=next_id())
	blog_id = StringField(ddl="varchar(50)")  # 博客id
	user_id = StringField(ddl="varchar(50)")  # 评论者id
	user_name = StringField(ddl="varchar(50)")  # 评论者名字
	user_image = StringField(ddl="varchar(500")  # 评论者上传的图片
	content = TextField()
	created_at = FloatField(default=time.time)





'''
	初始化数据库表
	如果表的数量很少，可以手写创建表的SQL脚本：

	-- schema.sql

	drop database if exists awesome;

	create database awesome;

	use awesome;

	grant select, insert, update, delete on awesome.* to 'www-data'@'localhost' identified by 'www-data';

	create table users (
	    `id` varchar(50) not null,
	    `email` varchar(50) not null,
	    `passwd` varchar(50) not null,
	    `admin` bool not null,
	    `name` varchar(50) not null,
	    `image` varchar(500) not null,
	    `created_at` real not null,
	    unique key `idx_email` (`email`),
	    key `idx_created_at` (`created_at`),
	    primary key (`id`)
	) engine=innodb default charset=utf8;

	create table blogs (
	    `id` varchar(50) not null,
	    `user_id` varchar(50) not null,
	    `user_name` varchar(50) not null,
	    `user_image` varchar(500) not null,
	    `name` varchar(50) not null,
	    `summary` varchar(200) not null,
	    `content` mediumtext not null,
	    `created_at` real not null,
	    key `idx_created_at` (`created_at`),
	    primary key (`id`)
	) engine=innodb default charset=utf8;

	create table comments (
	    `id` varchar(50) not null,
	    `blog_id` varchar(50) not null,
	    `user_id` varchar(50) not null,
	    `user_name` varchar(50) not null,
	    `user_image` varchar(500) not null,
	    `content` mediumtext not null,
	    `created_at` real not null,
	    key `idx_created_at` (`created_at`),
	    primary key (`id`)
	) engine=innodb default charset=utf8;


	如果表的数量很多，可以从Model对象直接通过脚本自动生成SQL脚本，使用更简单。

	把SQL脚本放到MySQL命令行里执行：
	$ mysql -u root -p < schema.sql





'''




























