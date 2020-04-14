import data
import errors
import parse
import os
import os.path

PRIVATE = 2
PROTECTED = 1
PUBLIC = 0

rw = lambda name: len(name) - len(name.lstrip('_'))

type_method = lambda type, *other: data.Method(lambda *args: type if not args or len(args) < len(other) else type(*other, *args))

def expr(val, scope):
    if val.type == 'string':
        return data.String(val.val[0])
    elif val.type == 'number':
        return data.Number(val.val[0])
    elif val.type == 'decl':
        t = data.call(data.get_name(scope, val.val[0]))
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
                default = data.call(t)
            except:
                default = t
        if len(val.val) == 3:
            func = data.get(scope, val.val[0]).to
            args = []
            for arg in val.val[2].val:
                if arg.type == 'decl':
                    args.append(arg)
                else:
                    args.append(expr(arg, scope))
            scope.set(data.Symbol(val.val[1]), data.call(func, *args))
        else:
            scope.set(data.Symbol(val.val[1]), default)
    elif val.type == 'name':
        return data.get_name(scope, val.val[0])
    elif val.type == 'call':
        func = expr(val.val[0], scope)
        args = []
        for arg in val.val[1].val:
            if arg.type == 'decl' or isinstance(data.ref(func), data.LazyMethod):
                args.append(arg)
            else:
                args.append(expr(arg, scope))
        return data.call(func, *args)
    elif val.type == 'op':
        a = expr(val.val[0], scope)
        func = data.op(a, data.Symbol(val.val[1]))
        return data.call(func, expr(val.val[2], scope))
    elif val.type == 'block':
        program = Program(val.val[0])
        return data.Block(program, scope)
    elif val.type == 'array':
        array = []
        for item in val.val[0].val:
            array.append(expr(item, scope))
        if val.val[0].val:
            return data.List(type(array[0]), *array)
        else:
            return data.List(data.Type)
    elif val.type == 'index':
        index = data.op(expr(val.val[0], scope), data.Symbol('index'))
        return data.call(index, expr(val.val[1], scope))
    elif val.type == 'child':
        return data.get(expr(val.val[0], scope), val.val[1])
    elif val.type == 'bool':
        if val.val[0] == 'true':
            return data.Bool(True)
        else:
            return data.Bool(False)

class Program():
    def __init__(self, ast):
        self.ast = ast
        self.globals = data.Map(data.Symbol, data.Type)
        self.globals.set(data.Symbol('import'), data.Method(self._import))
        self.globals.set(data.Symbol('if'), data.Method(self._if))
        self.globals.set(data.Symbol('while'), data.LazyMethod(self._while))
        self.globals.set(data.Symbol('return'), data.Method(lambda val: val))
        self.globals.set(data.Symbol('py'), data.Method(self.py))
        self.globals.set(data.Symbol('inf'), data.Number(float('inf')))
        self.globals.set(data.Symbol('infinity'), data.Number(float('inf')))
        self.globals.set(data.Symbol('number'), type_method(data.Number))
        self.globals.set(data.Symbol('string'), type_method(data.String))
        self.globals.set(data.Symbol('func'), type_method(data.Func, self.globals))
        self.globals.set(data.Symbol('class'), type_method(data.Class))
        self.globals.set(data.Symbol('list'), type_method(data.List))
        self.globals.set(data.Symbol('range'), type_method(data.Range))
        self.globals.set(data.Symbol('type'), type_method(data.Type))
        self.globals.set(data.Symbol('symbol'), type_method(data.Symbol))
        self.globals.set(data.Symbol('map'), type_method(data.Map))
        self.globals.set(data.Symbol('bool'), type_method(data.Bool))
        self.globals.set(data.Symbol('void'), data.Method(lambda: type(None)))
        self.globals.set(data.Symbol('_pytype'), type_method(data.PyType))
    def py(self, *args):
        code = args[0].val
        d = {**globals(), **self.globals.attrs}
        exec(f'out = {code}', d)
        return d['out']
    def print(self, *args): #recursion moment <----- recursion is its own reward
        for val in args: # also i found the problem
            print(data.call(data.get(val, '_string')).val) # i'm gonna fix it
    def _import(self, *args):
        name = args[0].val
        try:
            if name.startswith('stdlib'):
                file = open((__file__.rstrip('/src/runner.py') + f'/{name}.qyl').lstrip('/'))
            else:
                file = open(os.path.join(os.getcwd(), f'{name}.qyl'))
            ast = parse.Parser().parse(parse.Lexer().tokenize(file.read()))
            program = Program(ast)
            program.run()
            self.globals.set(data.Symbol(name.split('/')[-1]), program.globals)
        except FileNotFoundError:
            try:
                if name.startswith('stdlib'):
                    file = open((__file__.rstrip('/src/runner.py') + f'/{name}.py').lstrip('/'))
                else:
                    file = open(os.path.join(os.getcwd(), f'{name}.py'))
                out = {}
                exec(compile(file.read(), 'quill', 'exec'), out)
                map = data.Map(data.Symbol, data.Type)
                map.attrs.update(out['attrs'])
                self.globals.set(data.Symbol(name.split('/')[-1]), map)
            except FileNotFoundError:
                errors.error('File not found')
    def _if(self, *args):
        args[0].val.globals = self.globals
        if data.Bool(args[1]).val:
            return data.call(args[0])
    def _while(self, *args):
        args = list(args)
        args[0] = expr(args[0], self.globals)
        args[0].val.globals = self.globals
        out = None
        while data.Bool(expr(args[1], self.globals)).val:
            out = data.call(args[0])
        return out
    def run(self):
        if not self.ast.val:
            return
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
