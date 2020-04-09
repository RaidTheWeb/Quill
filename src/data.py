import errors

null = None

def convert(val, attr, fallback):
    if hasattr(val, 'attrs'):
        if attr in val.attrs:
            return val.attrs[attr].attrs['_call']().val
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
        return String(str(self.val))
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
        self.to.eq(self.to.attrs['_add'].attrs['_call'](val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def subeq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(self.to.attrs['_sub'].attrs['_call'](val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def muleq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(self.to.attrs['_mul'].attrs['_call'](val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def diveq(self, val):
        if isinstance(val, Reference):
            val = val.to
        typecheck(val, self.type, f'Invalid type for reference')
        self.to.eq(self.to.attrs['_div'].attrs['_call'](val))
        self.attrs.update(self.to.attrs)
        self.val = self.to.val
    def string(self):
        return self.to.string()

class Block(Type):
    typename = 'Block'
    def __init__(self, ast):
        self.val = ast
        self.typename = 'Block'
        self.attrs = {
            '_set':Method(super().set),
            '_get':Method(super().get),
            '_eq':Method(super().eq),
            '_call':Method(self.val.run),
            '_string':Method(self.string),
        }
    def string(self):
        return String(repr(self.val))

class Func(Type):
    typename = 'Func'
    def __init__(self, scope, block, *params):
        self.val = block
        self.val.val.globals = scope
        self.params = params[:-1] # what is expected
        self.typename = 'Func'
        if not params:
            self.res = Type
        else:
            last = params[-1]
            if isinstance(last, Reference):
                self.res = last.to.attrs['_call']
                if hasattr(self.res, 'attrs'):
                    self.res = self.res.attrs['_call']()
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
        for i in range(len(self.params)):
            param = self.params[i]
            name = param.val[1]
            t = self.val.val.globals.get(Symbol(param.val[0])).val()
            if isinstance(args[i], Reference):
                args[i] = args[i].to
            typecheck(args[i], t, f'Invalid argument type: expected {t.typename}, got {args[i].typename}')
            self.val.val.globals.set(Symbol(name), args[i])
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
        if val.val > len(self.val) - 1:
            errors.error('Index too high')
        return Reference(self.type, self.val[int(val.val)])
    def sort(self):
        self.val = sorted(self.val)
    def each(self, block, decl):
        type, name = decl.val
        for item in self.val:
            block.val.globals.attrs[name] = item
            block.val.run()

class Range(Type):
    def __init__(self, end, start=Number(0), increase=Number(1)):
        typecheck(end, Number, f'Invalid type for range end: expected number, got {end.typename}')
        self.typename = 'Range'
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
