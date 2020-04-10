import data
import errors
import parse

PRIVATE = 2
PROTECTED = 1
PUBLIC = 0

rw = lambda name: len(name) - len(name.lstrip('_'))

type_method = lambda type, *other: data.Method(lambda *args: type if not args or len(args) < len(other) else type(*other, *args))

op_names = {
    '+':['add'],
    '-':['sub'],
    '=':['eq'],
    '==':['cmp'],
    '>':['gt'],
    '<':['lt'],
    '*':['mul'],
    '/':['div'],
    '+=':['addeq'],
    '-=':['subeq'],
    '*=':['muleq'],
    '/=':['diveq'],
    'index':['index']
}

def ref(obj):
    if isinstance(obj, data.Reference):
        return obj.to
    return obj

def call(obj, *args):
    obj = ref(obj)
    if isinstance(obj, data.Method):
        return obj.attrs['_call'](*args)
    if get(obj, 'call', error=False):
        return get(obj, 'call').attrs['_call'](*args)
    elif get(obj, '_call', error=False):
        return get(obj, '_call').attrs['_call'](*args)
    else:
        errors.error(f'Object {obj.string().val} is not callable')

def get_name(scope, name):
    name = name.split('.')
    while name:
        part = name.pop(0)
        old = scope
        scope = get(scope, data.Symbol(part))
        if not scope:
            errors.error(f'Object {old.string().val} has no attribute {part}')
    return scope

def get(obj, attr, error=True):
    if not obj:
        errors.error('Object is null')
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
        t = call(get_name(scope, val.val[0]))
        if t == data.Number:
            default = data.Number(0)
        elif t == data.String:
            default = data.String('')
        elif t == data.Func:
            default = data.Func(scope, data.Block(Program(parse.Node('program'))))
            default.val.val.globals = scope
        elif t == data.Class:
            default = data.Class(data.Block(Program(parse.Node('program'))))
        elif t == data.List:
            default = data.List(data.Type)
        elif t == data.PyType:
            default = data.PyType(None)
        else:
            try:
                default = call(t)
            except:
                default = t
        scope.set(data.Symbol(val.val[1]), default)
    elif val.type == 'name':
        return get_name(scope, val.val[0])
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
        program = Program(val.val[0])
        for attr in scope.attrs:
            val = scope.attrs[attr]
            if isinstance(val, data.Map):
                program.globals.attrs[attr] = val
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
        self.globals.set(data.Symbol('return'), data.Method(lambda val: val))
        self.globals.set(data.Symbol('py'), data.Method(self.py))
        self.globals.set(data.Symbol('number'), type_method(data.Number))
        self.globals.set(data.Symbol('string'), type_method(data.String))
        self.globals.set(data.Symbol('func'), type_method(data.Func, self.globals))
        self.globals.set(data.Symbol('class'), type_method(data.Class))
        self.globals.set(data.Symbol('list'), type_method(data.List))
        self.globals.set(data.Symbol('range'), type_method(data.Range))
        self.globals.set(data.Symbol('type'), type_method(data.Type))
        self.globals.set(data.Symbol('symbol'), type_method(data.Symbol))
        self.globals.set(data.Symbol('map'), type_method(data.Map))
        self.globals.set(data.Symbol('void'), data.Method(lambda: type(None)))
        self.globals.set(data.Symbol('_pytype'), type_method(data.PyType))
    def py(self, *args):
        code = args[0].val
        d = {**globals(), **self.globals.attrs}
        exec(f'out = {code}', d)
        return d['out']
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
            try:
                out = {}
                exec(compile(open(f'{name}.py').read(), 'quill', 'exec'), out)
                map = data.Map(data.Symbol, data.Type)
                map.attrs.update(out['attrs'])
                self.globals.set(data.Symbol(name.split('/')[-1]), map)
            except FileNotFoundError:
                errors.error('File not found')
    def _if(self, *args):
        args[0].val.globals = self.globals
        if data.Bool(args[1]).val:
            return call(args[0])
    def run(self):
        try:
            for node in self.ast.val[:-1]:
                val = expr(node, self.globals)
                if val:
                    return val
            return expr(self.ast.val[-1], self.globals)
        except Exception as e:
            errors.error(f'Python threw error: {type(e).__name__} {e}')

def run(ast):
    Program(ast).run()
