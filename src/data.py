import errors

null = None

class Type():
	def __init__(self):
		self.val = None
		self.attrs = {
			'_set':Method(self.set),
			'_get':Method(self.get),
			'_=':Method(self.eq),
			'_string':Method(self.string),
			'_type':Method(self.type),
		}
	def set(self, symbol, val):
		if symbol.val in self.attrs:
			if not isinstance(self.attrs[symbol.val], type(val)):
				errors.error(f'Bad type for attribute {symbol.val}') # only called on error
			self.attrs[symbol.val] = val
		return val
	def get(self, symbol):
		return self.attrs.get(symbol.val, null)
	def eq(self, new):
		if not isinstance(new, self.__class__):
			errors.error(f'Invalid type for value')
		self.val = new.val
		self.attrs = new.attrs
	def string(self):
		return String(f'<Type {self.__class__.__name__}>')
	def type(self):
		return 'Type'

class Method(Type):
    def __init__(self, func):
        self.val = func
        self.attrs = {
            '_call':self.val,
            '_string':self.string,
        }
    def string(self):
        return String(f'<Method {id(self.val)}>')

class String(Type):
	def __init__(self, val):
		self.val = val.strip('"')
		self.attrs = {
			'_set':Method(super().set),
			'_get':Method(super().get),
			'_string':Method(self.string),
			'_type': Method(super().type()),
			'_index': Method(self.index),
			'_len': Method(self.len),
            '_add':Method(self.add),
		}
	def string(self):
		return self
	def index(self, index):
		if index.val > len(self.val) - 1:
			errors.error('Index too high')
		return String(self.val[int(index.val)])
	def len(self):
		return Number(len(self.val))
	def add(self, other):
		return String(self.val + other.val)

class Number(Type):
    def __init__(self, val):
        self.val = float(val)
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_string':Method(self.string),
            '_add':Method(self.add),
			'_type':Method(super().type),

        }
    def string(self):
        return String(str(self.val))
    def add(self, other):
        return Number(self.val + other.val)


class Symbol(Type):
    def __init__(self, val):
        if isinstance(val, Symbol):
            self.val = val.val
        else:
            self.val = val
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_string':Method(self.string),
			'_type':Method(super().type),
        }
    def string(self):
        return String(':' + self.val)

class Bool(Type):
    def __init__(self, val):
        self.val = bool(val.val)
        self.attrs = {
            '_set': Method(super().set),
            '_get': Method(super().get),
            '_string': Method(self.string),
            '_number': Method(self.number),
			'_type':Method(super().type),
        }

    def string(self):
        return String(str(self.val))

    def number(self):
        if self.val == True:
            return Number(1)
        else:
            return Number(0)


class Map(Type):
	def __init__(self, key_t, val_t):
		self.key_t = key_t
		self.val_t = val_t
		self.val = {}
		self.attrs = {
			'_set':Method(self.set),
			'_get':Method(self.get),
			'_string':Method(self.string),
			'_type':Method(super().type),
			'_index':Method(lambda val: self.get(Symbol(val.val))),
		}
	def set(self, symbol, val):
		if symbol.val in self.attrs:
			if type(self.attrs[symbol.val]) != type(val):
				errors.error(f'Invalid type for key {symbol.val}')
				self.attrs[symbol.val] = val
		else:
			self.attrs[symbol.val] = val
	def get(self, symbol):
		if symbol.val in self.attrs:
			return Reference(type(self.attrs[symbol.val]), self.attrs[symbol.val])
		else:
			errors.error(f'Invalid key {symbol.val}')
	def string(self):
		out = '{'
		for key in self.attrs:
			out += f'{key}:{self.attrs[key].string().val}, '
			out = out.rstrip(', ') + '}'
		return String(out)

class Reference(Type):
	def __init__(self, t, to):
		self.t = t
		self.to = to # the thing this is a reference to
		self.val = to.val
		self.attrs = self.to.attrs
		self.attrs['eq'] = Method(self.eq)
	def eq(self, val):
		if not isinstance(val, self.t): # this checks the type
			errors.error(f'Invalid type {val.type()}')
		self.to.eq(val)
		self.attrs.update(self.to.attrs)
		self.val = self.to.val
	def string(self):
		return self.to.string()

class Block(Type):
	def __init__(self, ast):
		self.val = ast
		self.attrs = {
			'_set':Method(super().set),
			'_get':Method(super().get),
			'_eq':Method(super().eq),
			'_call':self.val.run,
			'_string':self.string
		}
	def string(self):
		return String(repr(self.val))

class Func(Type):
	def __init__(self, scope, block, *params):
		self.val = block
		self.val.val.globals = scope
		self.params = params[:-1] # what is expected
		self.res = params[-1].val if params else lambda: Type
		self.attrs = {
			'_set':Method(super().set),
			'_get':Method(super().get),
			'_eq':Method(super().eq),
			'_call':self.call
		}
	def call(self, *args):
		if len(args) != len(self.params):
			errors.error('Wrong amount of arguments')
		for i in range(len(self.params)):
			param = self.params[i]
			name = param.val[1]
			t = self.val.val.globals.get(Symbol(param.val[0])).val()
			if type(args[i]) != t:
				errors.error('Invalid argument type')
			self.val.val.globals.set(Symbol(name), args[i])
		out = self.val.val.run()
		if isinstance(out, Reference):
			out = out.to
		if not isinstance(out, self.res()):
			errors.error('Invalid return type')
		return out
	def Return(val):
		pass

class Class(Type):
	def __init__(self, scope, block):
		self.val = block
		self.val.val.globals = scope
		self.attrs = {
			'_set': Method(self.set),
			'_get': Method(self.get),
			'_call':self.call,
			'_eq':Method(super().eq),
			'string':Method(self.string),
		}
	def set(self, symbol, val):
		self.val.val.globals.set(symbol, val)
	def get(self, symbol):
		if symbol.val in self.val.val.globals.attrs:
			return self.val.val.globals.attrs[symbol.val]
		return self.attrs.get(symbol.val, null)
	def call(self):
		new = Class(self.val.val.globals, self.val)
		new.attrs = self.attrs
		new.val.val.run()
		return new
	def string(self):
		return String(f'<Class {id(self.val)}>')


class List(Type):
	def __init__(self, type, *args):
		self.val = list(args)
		self.type = type
		self.attrs = {
			'_get':    Method(super().get),
			'_set':    Method(super().set),
			'_string': Method(self.string),
			'append':  Method(self.val.append),
			'_type':Method(lambda: String('List')),
			'_index':Method(self.index),
			'sort': Method(self.sort),
		}
		for arg in args:
			self.val.append(arg)

	def append(self, val):
		if not isinstance(val, self.type):
			errors.error("Invalid Type")
		else:
			self.val.append(val)

	def string(self):
		out = '['
		for item in self.val:
			out += item.string().val + ', '
		out = out.rstrip(', ') + ']'
		return String(out)
	def index(self, val):
		if not isinstance(val, Number):
			errors.error('Invalid index type')
		if val.val > len(self.val) - 1:
			errors.error('Index too high')
		return self.val[int(val.val)]
	def sort(self):
		self.val = sorted(self.val)

class Range(Type):
	def __init__(self, end, start=Number(0), increase = Number(1)):
		self.val = List(Number)
		for i in range(int(start.val), int(end.val), int(increase.val)):
			self.val.append(Number(i))

		self.attrs = {
			'_set':Method(super().set),
			'_get':Method(super().get),
			'_eq':Method(super().eq),
			'each':Method(self.each),
		}
	def each(self, block, decl):
		type, name = decl.val
		for item in self.val.val:
			block.val.globals.attrs[name] = item
			block.val.run()
