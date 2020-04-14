import errors
import copy

null = None

def convert(val, attr, fallback):
    if hasattr(val, 'attrs'):
        if attr in val.attrs:
            return get(val.attrs[attr], '_call')().val
        return val.val
    else:
        return fallback(val)

def typecheck(val, want, err='Invalid type'):
    if isinstance(want, Class):
        want = Class
    if want == PyType:
        return True
    if not isinstance(val, want):
        errors.error(err)
        return False
    return True

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
    if isinstance(obj, Reference):
        return obj.to
    return obj

def call(obj, *args):
    obj = ref(obj)
    if isinstance(obj, Method):
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
        scope = get(scope, Symbol(part))
        if not scope:
            errors.error(f'Object {old.string().val} has no attribute {part}')
    return scope

def get(obj, attr, error=True):
    if not obj:
        errors.error('Object is null')
    attr = Symbol(attr) # select it and use ctrl-[ and ctrl-]
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
    if not obj:
        errors.error('Object is null')
    if op.val not in obj.attrs:
        if op.val in op_names:
            for name in op_names[op.val]:
                if get(obj, name, error=False):
                    return get(obj, Symbol(name))
                elif get(obj, '_' + name, error=False):
                    return get(obj, Symbol('_' + name))
                else:
                    errors.error(f'{obj.string().val} does not have operator {op.string().val}')
        else:
            return get(obj, Symbol(op))

def copy(obj):
    if isinstance(obj, List):
        return List(obj.type, *obj.val)
    elif isinstance(obj, Block):
        return Block(obj.val, obj.parent)
    elif isinstance(obj, Map):
        out = Map(obj.key_t, obj.val_t)
        out.attrs = obj.attrs
        return out
    else:
        return type(obj)(obj.val)

class Type():
    typename = 'Type'
    def __init__(self):
        self.val = None
        self.typename = 'Type'
        self.attrs = {
            '_set':Method(self.set),
            '_get':Method(self.get),
            '_eq':Method(self.eq),
            '_string':Method(self.string),
            '_type':Method(self.type),
            '_cmp':Method(self.cmp),
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
        typecheck(new, self.__class__, f'Invalid type for value')
        self.val = new.val
        self.attrs = new.attrs
    def string(self):
        return String(f'<Type {self.__class__.__name__}>')
    def cmp(self, other):
        return Bool(self.val == other.val)
    def type(self):
        return 'Type'

class PyType(Type):
    typename = '_PyType'
    def __init__(self, val):
        self.val = val
        self.typename = '_PyType'
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_eq':Method(super().eq),
        }

class Method(Type):
    typename = 'Method'
    def __init__(self, func):
        self.val = func
        self.typename = 'Method'
        self.attrs = {
            '_call':self.val,
            '_string':self.string,
        }
    def string(self):
        return String(f'<Method {id(self.val)}>')

class LazyMethod(Method):
    pass

class String(Type):
    typename = 'String'
    def __init__(self, val):
        self.val = convert(val, '_string', lambda val: val.strip('"')).replace('\\r', '\r').replace('\\n', '\n')
        self.typename = 'String'
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_string':Method(self.string),
            '_type': Method(super().type()),
            '_index': Method(self.index),
            '_len': Method(self.len),
            '_cmp':Method(super().cmp),
            '_add':Method(self.add),
            '_symbol':Method(lambda: Symbol(self.val)),
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
    def each(self, block, decl):
        type, name = decl.val
        for item in self.val:
            block.val.globals.attrs[name] = String(item)
            block.val.run()

class Number(Type):
    typename = 'Number'
    def __init__(self, val):
        self.val = convert(val, '_number', float)
        self.typename = 'Number'
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_string':Method(self.string),
            '_add':Method(self.add),
            '_sub':Method(self.sub),
            '_mul':Method(self.mul),
            '_div':Method(self.div),
            '_cmp':Method(super().cmp),
            '_gt':Method(self.gt),
            '_lt':Method(self.lt),
            '_type':Method(super().type),
        }
    def string(self):
        return String(str(self.val))
    def add(self, other):
        return Number(self.val + other.val)
    def sub(self, other):
        return Number(self.val - other.val)
    def mul(self, other):
        return Number(self.val * other.val)
    def div(self, other):
        return Number(self.val / other.val)
    def gt(self, other):
        return Bool(self.val > other.val)
    def lt(self, other):
        return Bool(self.val < other.val)

class Symbol(Type):
    typename = 'Symbol'
    def __init__(self, val):
        self.val = convert(val, '_symbol', lambda val: String(val).val)
        self.typename = 'Symbol'
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_string':Method(self.string),
            '_type':Method(super().type),
            '_add':Method(self.add),
            '_cmp':Method(super().cmp),
        }
    def string(self):
        return String(':' + self.val)
    def add(self, other):
        return Symbol(self.val + other.val)

class Bool(Type):
    typename = 'Bool'
    def __init__(self, val):
        self.val = convert(val, '_bool', bool)
        self.typename = 'Bool'
        self.attrs = {
            '_set': Method(super().set),
            '_get': Method(super().get),
            '_string': Method(self.string),
            '_number': Method(self.number),
            '_type':Method(super().type),
            '_add':Method(self.add),
            '_sub':Method(self.sub),
            '_mul':Method(self.mul),
            '_cmp':Method(super().cmp),
            '_div':Method(self.div),
        }
    def string(self):
        return String(str(self.val).lower())
    def number(self):
        if self.val == True:
            return Number(1)
        else:
            return Number(0)
    def add(self, other):
        return Number(self.val + other.val)
    def sub(self, other):
        return Number(self.val - other.val)
    def mul(self, other):
        return Number(self.val * other.val)
    def div(self, other):
        return Number(self.val / other.val)

class Map(Type):
    typename = 'Map'
    def __init__(self, key_t, val_t):
        self.key_t = key_t
        self.val_t = val_t
        self.val = {}
        self.typename = 'Map'
        self.attrs = {
            '_set':Method(self.set),
            '_get':Method(self.get),
            '_string':Method(self.string),
            '_cmp':Method(super().cmp),
            '_type':Method(super().type),
            '_index':Method(lambda val: self.get(Symbol(val))),
            'each':Method(self.each),
        }
    def set(self, symbol, val):
        if symbol.val in self.attrs:
            typecheck(self.attrs[symbol.val], type(val), f'Invalid type for key {symbol.val}')
            self.attrs[symbol.val] = val
        else:
            self.attrs[symbol.val] = val
    def get(self, symbol):
        if symbol.val in self.attrs:
            return Reference(type(self.attrs[symbol.val]), self.attrs[symbol.val])
        else:
            return None
    def string(self):
        return String(f'<Map {self.key_t.typename}, {self.val_t.typename}>')
    def each(self, block, decl):
        type, name = decl.val
        for item in self.attrs:
            block.val.globals.attrs[name] = item
            block.val.run()

class Reference(Type):
    typename = 'Reference'
    def __init__(self, type, to):
        self.type = type
        self.to = to # the thing this is a reference to
        self.val = to.val
        self.attrs = self.to.attrs
        self.attrs['_eq'] = Method(self.eq)
        self.attrs['_addeq'] = Method(self.addeq)
        self.attrs['_subeq'] = Method(self.subeq)
        self.attrs['_muleq'] = Method(self.muleq)
        self.attrs['_diveq'] = Method(self.diveq)
        self.typename = to.typename
    def eq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(val)
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def addeq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(get(get(self.to, '_add'), '_call')(val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def subeq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(get(get(self.to, '_sub'), '_call')(val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def muleq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(get(get(self.to, '_mul'), '_call')(val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def diveq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(get(get(self.to, '_div'), '_call')(val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def string(self):
        return self.to.string()

class Block(Type):
    typename = 'Block'
    def __init__(self, ast, scope=None):
        self.val = ast
        self.parent = scope
        self.scope = ast.globals
        self.typename = 'Block'
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_eq':Method(super().eq),
            '_call':Method(self.val.run),
            '_string':Method(self.string),
        }
        self.val.globals.attrs['_get'] = Method(self.get)
    def string(self):
        return String(repr(self.val))
    def get(self, attr):
        if attr.val in self.scope.attrs:
            return self.scope.get(attr)
        elif attr.val in self.parent.attrs:
            val = self.parent.get(attr).to
            self.scope.set(attr, copy(val))
            return self.scope.get(attr)
        else:
            errors.error(f'No such local {attr.val}')

class Func(Type):
    typename = 'Func'
    def __init__(self, scope, block, *params):
        self.val = block
        self.params = params[:-1] # what is expected
        self.typename = 'Func'
        if not params:
            self.res = Type
        else:
            last = params[-1]
            if isinstance(last, Reference):
                self.res = get(last.to, '_call')
                if hasattr(self.res, 'attrs'):
                    self.res = get(self.res, '_call')()
                else:
                    self.res = self.res()
            else:
                self.res = type(last)
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_eq':Method(super().eq),
            '_call':Method(self.call),
        }
    def call(self, *args):
        args = list(args)
        if len(args) != len(self.params):
            errors.error('Wrong amount of arguments')
            return
        for i in range(len(self.params)):
            param = self.params[i]
            name = param.val[1]
            t = self.val.scope.get(Symbol(param.val[0])).val()
            if isinstance(args[i], Reference):
                args[i] = args[i].to
            if not typecheck(args[i], t, f'Invalid argument type: expected {t.typename}, got {args[i].typename}'):
                return
            self.val.scope.set(Symbol(name), args[i])
        out = self.val.val.run()
        if isinstance(out, Reference):
            out = out.to
        if type(out) != Type:
            if self.res == type(None):
                if out:
                    errors.error(f'Expected no return value, got {out.typename}')
            else:
                typecheck(out, self.res, f'Invalid return type: expected {self.res.typename}, got {out.typename}')
        return out
    def Return(val):
        pass

class Class(Type):
    def __init__(self, block):
        self.val = block
        self.typename = 'Class'
        self.attrs = {
            '_set': Method(self.set),
            '_get': Method(self.get),
            '_call':Method(self.call),
            '_eq':Method(super().eq),
            '_string':Method(self.string),
        }
    def set(self, symbol, val):
        self.val.val.globals.set(symbol, val)
    def get(self, symbol):
        if symbol.val in self.val.val.globals.attrs:
            return self.val.val.globals.get(symbol)
        return self.attrs.get(symbol.val, null)
    def call(self):
        new = Class(self.val)
        new.attrs = self.attrs
        new.val.val.globals.attrs = self.val.val.globals.attrs
        new.val.val.run()
        return new
    def string(self):
        return String(f'<Class {id(self.val)}>')


class List(Type):
    def __init__(self, type, *args):
        if isinstance(type, Reference):
            type = get(type.to, '_call')()
        for arg in args:
            typecheck(arg, type, f'Invalid type for list item: expected {type.typename}, got {arg.typename}')
        self.val = list(args)
        self.type = type
        self.typename = 'List'
        self.attrs = {
            '_get':Method(super().get),
            '_set':Method(super().set),
            '_string':Method(self.string),
            'append':Method(self.val.append),
            '_type':Method(lambda: String('List')),
            '_index':Method(self.index),
            'each':Method(self.each),
            'sort': Method(self.sort),
        }
    def append(self, val):
        typecheck(val, self.type, f'Invalid type for list item: expected {self.type.typename}, got {val.typename}')
        self.val.append(val)
    def string(self):
        out = '['
        for item in self.val:
            out += item.string().val + ', '
        out = out.rstrip(', ') + ']'
        return String(out)
    def index(self, val):
        if isinstance(val, Reference):
            val = val.to
        if not isinstance(val, Number):
            errors.error('Invalid index type')
            return
        if val.val > len(self.val) - 1 or not self.val:
            errors.error('Index too high')
            return
        return Reference(self.type, self.val[int(val.val)])
    def sort(self):
        self.val = sorted(self.val)
    def each(self, block, decl):
        type, name = decl.val
        for item in self.val:
            block.val.globals.attrs[name] = item
            block.val.run()

class Range(Type):
    def __init__(self, end, start=Number(0), inc=Number(1)):
        end = ref(end)
        typecheck(end, Number, f'Invalid type for range end: expected number, got {end.typename}')
        self.typename = 'Range'
        self.val = start
        self.end = end
        self.inc = inc

        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_eq':Method(super().eq),
            'each':Method(self.each),
        }
    def each(self, block, decl):
        type, name = decl.val
        while self.val.lt(self.end).val:
            block.val.globals.attrs[name] = Number(self.val.val)
            block.val.run()
            self.val.val += self.inc.val
