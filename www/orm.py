#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'zspeng'

import asyncio,logging
#aiomysql是MySQL的python异步驱动程序,操作数据库要用到
import aiomysql

'''
由于Web框架使用了基于asyncio的aiohttp，这是基于协程的异步模型。在协程中，不能调用普通的同步IO操作，因为所有用户都是由一个线程服务的，
协程的执行速度必须非常快，才能处理大量用户的请求。而耗时的IO操作不能在协程中以同步的方式调用，否则，等待一个IO操作时，系统无法响应任何
其他用户。
这就是异步编程的一个原则：一旦决定使用异步，则系统每一层都必须是异步，“开弓没有回头箭”。
幸运的是aiomysql为MySQL数据库提供了异步IO的驱动。

'''
#这个函数的作用是输出信息，让你知道这个时间点程序在做什么
def log(sql,args=()):
	logging.info('SQL: %s' % sql)

#创建一个全局的连接池
#每个HTTP请求都可以从连接池中直接获取数据库连接。使用连接池的好处是不必频繁地打开和关闭数据库连接，而是能复用就尽量复用。
# 这个函数将来会在app.py的init函数中引用
#连接池由全局变量__pool存储，缺省情况下将编码设置为utf8，自动提交事务
@asyncio.coroutine
def create_pool(loop,**kw):	
	logging.info('create database connection pool...')
	#声明变量__pool是一个全局变量,如果不加声明,__pool则会被认为是私有变量,不能被其他函数引用
	global __pool
	# 调用一个自协程来创建全局连接池，create_pool的返回值是一个pool实例对象
	__pool = yield from aiomysql.create_pool(
		# 下面就是创建数据库连接需要用到的一些参数，从**kw（关键字参数）中取出来
        # kw.get的作用是，当没有传入参数是，默认参数就是get函数的第二项
		host = kw.get('host','localhost'),	# 数据库服务器位置，默认设在本地
		port = kw.get('port',3306),		# mysql的端口，默认设为3306
		user = kw['user'],		# 登陆用户名，通过关键词参数传进来。
		password = kw['password'],	# 登陆密码，通过关键词参数传进来
		db = kw['db'],		# 当前数据库名
		charset = kw.get('charset','utf8'),		# 设置编码格式，默认为utf-8
		autocommit = kw.get('autocommit',True),		# 自动提交模式，设置默认开启
		maxsize = kw.get('maxsize',10),		# 最大连接数默认设为10
		minsize = kw.get('minsize',1),		# 最小连接数，默认设为1，这样可以保证任何时候都会有一个数据库连接
		loop = loop		 # 传递消息循环对象，用于异步执行

	)


# =================================以下是SQL函数处理区====================================	
# select和execute方法是实现其他Model类中SQL语句都经常要用的方法


#要执行SELECT语句，我们用select函数执行，需要传入SQL语句和SQL参数：
async def select(sql,args,size=None):
	log(sql,args)
	global __pool	
	# 从连接池中获得一个数据库连接
    # 用with语句可以封装清理（关闭conn)和处理异常工作
	async with __pool.get() as conn:
	# with (yield from __pool) as conn:	
	# 	cur = yield from conn.cursor(aiomysql.DictCursor)
	# 	yield from cur.execute(sql.replace('?', '%s'), args or ())
		# 等待连接对象返回DictCursor可以通过dict的方式获取数据库对象，需要通过游标对象执行SQL
		async with conn.cursor(aiomysql.DictCursor) as cur:
			# 设置执行语句，其中sql语句的占位符为？，而python为%s, 这里要做一下替换
            # args是sql语句的参数
			await cur.execute(sql.replace('?','%s'),args or ())
			# 如果制定了查询数量，则查询制定数量的结果，如果不指定则查询所有结果
			if size:
				rs = await cur.fetchmany(size)		# 从数据库获取指定的行数
			else:
				rs = await cur.fetchall()		# 返回所有结果集
		logging.info('rows returned: %s' % len(rs))
		return rs 			# 返回结果集

# 定义execute()函数执行insert update delete语句;因为这3种SQL的执行都需要相同的参数，以及返回一个整数表示影响的行数：
async def execute(sql,args,autocommit=True):
	# execute()函数只返回结果数，不返回结果集，适用于insert, update这些语句
	log(sql)
	async with __pool.get() as conn:
		if not autocommit:
			await conn.begin()
		try:
			async with conn.cursor(aiomysql.DictCursor) as cur :
				await cur.execute(sql.replace('?','%s'),args)
				affected = cur.rowcount		# 返回受影响的行数
			if not autocommit:
				await conn.commit()
		except BaseException as e:
			if not autocommit:
				await conn.rollback()
			raise
		return affected						

# 这个函数在元类中被引用，作用是创建一定数量的占位符
def create_args_string(num):
	L = []
	for n in range(num):
		L.append('?')
	#比如说num=3，那L就是['?','?','?']，通过下面这句代码返回一个字符串'?,?,?'	
	return ', '.join(L)	




#有了基本的select()和execute()函数，我们就可以开始编写一个简单的ORM了。
#设计ORM需要从上层调用者角度来设计。


# =====================================Field定义域区==============================================
# 首先来定义Field类，它负责保存数据库表的字段名和字段类型

# 父定义域，可以被其他定义域继承
class Field(object):
	# 定义域的初始化，包括属性（列）名，属性（列）的类型，主键，默认值
	def __init__(self,name,column_type,primary_key,default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default			# 如果存在默认值，在getOrDefault()中会被用到
	
	# 定制输出信息为 类名，列的类型，列名;直接打印实例时用到
	def __str__(self):
		return '<%s,%s:%s>' % (self.__class__name__,self.column_type,self.name)


class StringField(Field):
	#ddl是数据定义语言("data definition languages")，默认值是'varchar(100)'，意思是可变字符串，长度为100
    #和char相对应，char是固定长度，字符串长度不够会自动补齐，varchar则是多长就是多长，但最长不能超过规定长度
	def __init__(self, name=None, primary_key=False, default=None, dd1='varchar(100)'):
		super().__init__(name,ddl,primary_key,default)
		#基类改为旧式类，即不继承任何基类	
		#super()采用新式类，要求最顶层的父类一定要继承于object，这样就可以利用super()函数来调用父类的init()等函数
		#每个父类都执行且执行一次，并不会出现重复调用的情况。而且在子类的实现中，不用到处写出所有的父类名字，符合DRY原则。	
		#如果是本身就会依次继承下一个类


class BooleanField(Field):

	def __init__(self, name=None, default=False):
		super().__init__(name, 'boolean', False, default)

class IntegerField(Field):

	def __init__(self, name=None, primary_key=False, default=0):
		super().__init__(name, 'bigint', primary_key, default)		


class FloatField(Field):

	def __init__(self, name=None, primary_key=False, default=0.0):
		super().__init__(name, 'real', primary_key, default)

class TextField(Field):

	def __init__(self, name=None, default=None):
		super().__init__(name, 'text', False, default)



# =====================================Model基类区==========================================


# 编写元类
#Model只是一个基类，将具体的子类如User的映射信息读取出来是通过metaclass：ModelMetaclass

class ModelMetaclass(type):

	def __new__(cls, name, bases, attrs):
		# 排除Model类本身
		if name=='Model':
			return type.__new__(cls, name, bases, attrs)
		# 获取table名称	
		tableName = attrs.get('__table__', None) or name 
		logging.info('found model: %s (table: %s)' % (name, tableName))
		# 获取所有定义域中的属性和主键
		mappings = dict()
		fields = []
		primaryKey = None 
		for k, v in attrs.items():
			if isinstance(v, Field):
				#找主键
				# 先判断找到的映射是不是主键
				if v.primary_key:	# 若主键已存在,又找到一个主键,将报错,每张表有且仅有一个主键
					raise StandardError('Duplicate primary key for field:%s' % k)	
				primaryKey = k
			else:
				fields.append(k)
		# 如果没有找到主键，也会报错		
		if not primaryKey:
			raise StandardError('Primary key not found.')	
		# 定义域中的key值已经添加到fields里了，就要在attrs中删除，避免重名导致运行时错误	
		for k in mappings.keys():
			attrs.pop(k)
		# 将非主键的属性变形,放入escaped_fields中,方便sql语句的书写	
		escaped_fields = list(map(lambda f: '`%s`' % f, fields))
		attrs['__mappings__'] = mappings 	#保存属性和列的映射关系
		attrs['__table__'] = tableName		# 表名
		attrs['__primary_key__'] = primaryKey 	#主键属性名
		attrs['__fields__'] = fields 	#除主键之外的属性名
		# 构造默认的SELECT, INSERT, UPDATE, DELETE语句
        # 以下都是sql语句
		attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f),fields)), primaryKey)
		attrs['__delete__']	= 'delete from `%s` where `%s`=?' % (tableName,primaryKey)
		return type.__new__(cls, name, bases, attrs)				



# =====================================Model基类区==========================================

#首先要定义的是所有ORM映射的基类Model：
# 定义所有ORM映射的基类Model， 使他既可以像字典那样通过[]访问key值，也可以通过.访问key值
#Model从dict继承，所以具备所有dict的功能，同时又实现了特殊方法__getattr__()和__setattr__()，因此又可以像引用普通字段那样写：
# 继承dict是为了使用方便，例如对象实例user['id']即可轻松通过UserModel去数据库获取到id
# 元类自然是为了封装我们之前写的具体的SQL处理函数，从数据库获取数据
# ORM映射基类,通过ModelMetaclass元类来构造类

class Model(dict, metaclass=ModelMetaclass):

	def __init__(self, **kw):
		# 这里直接调用了Model的父类dict的初始化方法，把传入的关键字参数存入自身的dict中
		super(Model,self).__init(**kw)

	# 获取dict的key
	def __getattr__(self, key):
		try:
			return self[key]
		except	KeyError:
			raise AttributeError(r" 'Model' object has no attribute '%s'" % key)

	# 设置dict的值的，通过d.k = v 的方式		
	def __setattr__(self,key,value):
		self[key] = value
	# 获取某个具体的值即Value,如果不存在则返回Non
	def getValue(self, key, value):
		# getattr(object, name[, default]) 根据name(属性名）返回属性值，默认为None
		#获取对象object的属性或者方法，如果存在打印出来，如果不存在，打印出默认值，默认值可选。
		# 需要注意的是，如果是返回的对象的方法，返回的是方法的内存地址，如果需要运行这个方法，
		# 可以在后面添加一对括号。
		return getattr(self, key, None)

	def getValueOrDefault(self,key):
		value = getattr(self, key, None)
		if value is None:
			# self.__mapping__在metaclass中，用于保存不同实例属性在Model基类中的映射关系
            # field是一个定义域!
			field = self.__mappings__[key]
			# 如果field存在default属性，那可以直接使用这个默认值
			if field.default is not None:
				# 如果field的default属性是callable(可被调用的)，就给value赋值它被调用后的值，如果不可被调用直接返回这个值
				value = field.default() if callable(field.default) else field.default	
				logging.debug('using default value for %s: %s' % (key,str(value)))
				# 把默认值设为这个属性的值
				setattr(self, key, value)	#给对象的属性赋值，若属性不存在，先创建再赋值。

		return value	

	# ==============往Model类添加类方法，就可以让所有子类调用类方法=================	


	@ classmethod  # 这个装饰器是类方法的意思，即可以不创建实例直接调用类方法
    async def find(cls, pk):
        '''查找对象的主键'''
        # select函数之前定义过，这里传入了三个参数分别是之前定义的 sql、args、size
        rs = await select("%s where `%s`=?" % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    # findAll() - 根据WHERE条件查找
	@classmethod	# 这个装饰器是类方法的意思，即可以不创建实例直接调用类方法
	async def findAll(cls, where=None, args=None, **kw):
		'find objects by where clause'
		sql = [cls.__select__]
		# 如果有where参数就在sql语句中添加字符串where和参数where
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:	# 这个参数是在执行sql语句前嵌入到sql语句中的，如果为None则定义一个空的list
			args = []
		# 如果有OrderBy参数就在sql语句中添加字符串OrderBy和参数OrderBy，但是OrderBy是在关键字参数中定义的	
		orderBy = kw.get('orderBy', None)
		if orderBy:
			sql.append('order by')
			sql.append(orderBy)
		limit = kw.get('limit', None)
		if limit is not None:
			sql.append('limit')
			if isinstance (limit, int):
				sql.append('?')
				args.append(limit)
			elif isinstance (limit, tuple) and len(limit) ==2:
				sql.append('?, ?')
				args.extend(limit)	# extend() 函数用于在列表末尾一次性追加另一个序列中的多个值（用新列表扩展原来的列表）。
			else:
				raise ValueError('Invalid limit value:%s' % str(limit))
		rs = await select(' '.join(sql), args)
		return [cls(**r) for r in rs]								

	# findNumber() - 根据WHERE条件查找，但返回的是整数，适用于select count(*)类型的SQL。
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append("where")
            sql.append(where)
        rs = await select(" ".join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    # ===============往Model类添加实例方法，就可以让所有子类调用实例方法===================

    # save、update、remove这三个方法需要管理员权限才能操作，所以不定义为类方法，需要创建实例之后才能调用
    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))  # 将除主键外的属性名添加到args这个列表中
        args.append(self.getValueOrDefault(self.__primary_key__))  # 再把主键添加到这个列表的最后
        rows = await execute(self.__insert__, args)
        if rows != 1:  # 插入纪录受影响的行数应该为1，如果不是1 那就错了
            logging.warn("无法插入纪录，受影响的行：%s" % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)














