import data
import errors
import parse

PRIVATE = 2
PROTECTED = 1
PUBLIC = 0

rw = lambda name: len(name) - len(name.lstrip('_'))

op_names = {
    '+':['add'],
    '=':['eq'],
	'index':['index']
}

def call(obj, *args):
	if get(obj, 'call', error=False):
		return get(obj, 'call')(*args)
	elif get(obj, '_call', error=False):
		return get(obj, '_call')(*args)
	else:
		errors.error(f'Object {obj.string().val} is not callable')


def get(obj, attr, error=True):
	attr = data.Symbol(attr) # select it and use ctrl-[ and ctrl-]
	if 'get' in obj.attrs:
		return call(obj.attrs['get'], attr)
	elif '_get' in obj.attrs:
		return call(obj.attrs['_get'], attr)
	elif attr.val in obj.attrs:
		return obj.attrs[attr.val]
	else:
		if error:
			errors.error(f'Cannot get attribute of object {obj.string().val}')
		else:
			return

def op(obj, op):
	if op.val not in obj.attrs:
		if op.val in op_names:
			for name in op_names[op.val]:
				if get(obj, name, error=False):
					return get(obj, data.Symbol(name))
				elif get(obj, '_' + name, error=False):
					return get(obj, data.Symbol('_' + name))
				else:
					errors.error(f'{obj.string().val} does not have operator {op.string().val}')
		else:
			return get(obj, data.Symbol(op))

def expr(val, scope):
	if val.type == 'string':
	    return data.String(val.val[0])
	elif val.type == 'number':
	    return data.Number(val.val[0])
	elif val.type == 'decl':
		t = call(get(scope, data.Symbol(val.val[0])))
		if t == data.Number:
			default = data.Number(0)
		elif t == data.String:
			default = data.String('')
		elif t == data.Func:
			default = data.Func(scope, data.Block(Program(parse.Node('program'))))
			default.val.val.globals = scope
		elif t == data.Class:
			default = data.Class(scope, data.Block(Program(parse.Node('program'))))
			default.val.val.globals = scope
		elif t == data.List:
			default = data.List(data.Type)
		else:
			default = data.Type()
		scope.set(data.Symbol(val.val[1]), default)
	elif val.type == 'name':
		name = val.val[0].split('.')
		while name:
			part = name.pop(0)
			old = scope
			scope = get(scope, data.Symbol(part))
			if not scope:
				errors.error(f'Object {old.string().val} has no attribute {part}')
		return scope
	elif val.type == 'call':
		func = expr(val.val[0], scope)
		args = []
		for arg in val.val[1].val:
			if arg.type == 'decl':
				args.append(arg)
			else:
				args.append(expr(arg, scope))
		return call(func, *args)
	elif val.type == 'op':
		a = expr(val.val[0], scope)
		func = op(a, data.Symbol(val.val[1]))
		return call(func, expr(val.val[2], scope))
	elif val.type == 'block':
		program = Program(val.val[0]);
		program.globals = scope
		return data.Block(program)
	elif val.type == 'array':
		array = []
		for item in val.val[0].val:
			array.append(expr(item, scope))
		return data.List(type(array[0]), *array)
	elif val.type == 'index':
		index = op(expr(val.val[0], scope), data.Symbol('index'))
		return call(index, expr(val.val[1], scope))
	elif val.type == 'child':
		return get(expr(val.val[0], scope), val.val[1])

class Program():
	def __init__(self, ast):
		self.ast = ast
		self.globals = data.Map(data.Symbol, data.Type)
		self.globals.set(data.Symbol('import'), data.Method(self._import))
		self.globals.set(data.Symbol('if'), data.Method(self._if))
		self.globals.set(data.Symbol('number'), data.Method(lambda: data.Number))
		self.globals.set(data.Symbol('string'), data.Method(lambda: data.String))
		self.globals.set(data.Symbol('return'), data.Method(lambda val: val))
		self.globals.set(data.Symbol('func'), data.Method(lambda *args: data.Func if not args else data.Func(self.globals, *args)))
		self.globals.set(data.Symbol('class'), data.Method(lambda *args: data.Class if not args else data.Class(self.globals, *args)))
		self.globals.set(data.Symbol('list'), data.Method(lambda *args: data.List if not args else data.List(*args)))
		self.globals.set(data.Symbol('range'), data.Method(lambda *args: data.Range if not args else data.Range(*args)))
		self.globals.set(data.Symbol('type'), data.Method(lambda *args: data.Type if not args else data.Type(*args)))
		self.globals.set(data.Symbol('symbol'), data.Method(lambda *args: data.Symbol if not args else data.Symbol(*args)))
		self.globals.set(data.Symbol('map'), data.Method(lambda *args: data.Map if not args else data.Map(*args)))
		self.globals.set(data.Symbol('void'), data.Method(lambda: type(None)))
		self.globals.set(data.Symbol('py'), data.Method(lambda x: eval(x.val)))

	def print(self, *args): #recursion moment <----- recursion is its own reward
		for val in args: # also i found the problem
			print(call(get(val, '_string')).val) # i'm gonna fix it
	def _import(self, *args):
		name = args[0].val
		try:
			file = open(f'{name}.qyl')
			ast = parse.Parser().parse(parse.Lexer().tokenize(file.read()))
			program = Program(ast)
			program.run()
			self.globals.set(data.Symbol(name.split('/')[-1]), program.globals)
		except FileNotFoundError:
			errors.error('File not found')
	def _if(self, *args):
		args[0].val.globals = self.globals
		if data.Bool(args[1]).val:
			call(args[0])
	def run(self):
		for node in self.ast.val[:-1]:
			expr(node, self.globals)
		return expr(self.ast.val[-1], self.globals)


def run(ast):
    Program(ast).run()
