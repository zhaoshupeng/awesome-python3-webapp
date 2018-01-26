


import math
def move(x,y,step,angle=0):
	nx = x + step * math.cos(angle)
	ny = y - step * math.sin(angle)
	return nx,ny





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
		# for k, v in attrs.items():
		# 	if isinstance(v, Field):
		# 		#找主键
		# 		# 先判断找到的映射是不是主键
		# 		if v.primary_key:	# 若主键已存在,又找到一个主键,将报错,每张表有且仅有一个主键
		# 			raise RuntimeError('Duplicate primary key for field:%s' % k)	
		# 		primaryKey = k
		# 	else:
		# 		fields.append(k)
		for k, v in attrs.items():
			if isinstance(v, Field):
				logging.info('  found mapping: %s ==> %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					# 找到主键:
					if primaryKey:
						raise StandardError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.append(k)

		# 如果没有找到主键，也会报错		
		if not primaryKey:
			raise RuntimeError('Primary key not found.')	
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





















