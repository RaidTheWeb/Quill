import sly
import errors

class Node():
    def __init__(self, type, *val):
        self.type = type
        self.val = list(val)
    def __repr__(self):
        return self.string(0).rstrip('\n')
    def string(self, n):
        out = f'{"    " * n}{self.type}\n'
        for value in self.val:
            if isinstance(value, Node):
                out += value.string(n + 1)
            else:
                out += f'{"    " * (n + 1)}{value}\n'
        return out

class Lexer(sly.Lexer):
    tokens = {NEWLINE, BOOL, NAME, STRING, SYMBOL, NUMBER}
    ignore = ' \t'
    ignore_comment = r'#.*?'
    literals = { "(", ")", "{", "}", ",", ".", ":", "[", "]"}

    NEWLINE = r'\n'
    STRING = r'".*?"'
    BOOL = r'(true|false)'
    NUMBER = r'-?[0-9]+(\.[0-9]+)?'
    SYMBOL = r':[^ \t\n(){}".,:\]\[]+(\.[^ \t\n(){}".:,+\]\[]+)*'
    NAME = r'[^ \t\n(){}".,:\]\[]+(\.[^ \t\n(){}".,:+\]\[]+)*' # here

    def error(self, t):
        errors.error('Syntax error')

class Parser(sly.Parser):
    tokens = Lexer.tokens

    def error(self, t):
        errors.error('Syntax error')

    @_('')
    def program(self, t):
        return Node('program')

    @_('statement')
    def program(self, t):
        return Node('program', t.statement)

    @_('program NEWLINE program')
    def program(self, t):
        return Node('program', *t.program0.val, *t.program1.val)

    @_('"[" list "]"')
    def expr(self, t):
        return Node('array', t.list) # stop don't change that

    @_('expr "(" list ")"')
    def expr(self, t):
        return Node('call', t.expr, t.list)

    @_('NAME ":" NAME')
    def expr(self, t):
        return Node('decl', t.NAME0, t.NAME1)

    @_('NAME ":" NAME "(" list ")"')
    def expr(self, t):
        return Node('decl', t.NAME0, t.NAME1, t.list)

    @_('expr "(" list ")" "{" program "}"')
    def expr(self, t):
        return Node('call', t.expr, Node('list', Node('block', t.program), *t.list.val))

    @_('expr NAME expr')
    def expr(self, t):
        return Node('op', t.expr0, t.NAME, t.expr1)

    @_('expr "[" expr "]"')
    def expr(self, t):
        return Node('index', t.expr0, t.expr1)

    @_('expr')
    def statement(self, t):
        return t.expr

    @_('BOOL')
    def expr(self, t):
        return Node('bool', t.BOOL)

    @_('')
    def list(self, t):
        return Node('list')

    @_('expr')
    def list(self, t):
        return Node('list', t.expr)

    @_('list "," list')
    def list(self, t):
        return Node('list', *t.list0.val, *t.list1.val)

    @_('"{" program "}"')
    def expr(self, t):
        return Node('block', t.program)

    @_('NAME')
    def expr(self, t):
        return Node('name', t.NAME)

    @_('SYMBOL')
    def expr(self, t):
        return Node('symbol', t.SYMBOL)

    @_('STRING')
    def expr(self, t):
        return Node('string', t.STRING)

    @_('NUMBER')
    def expr(self, t):
        return Node('number', t.NUMBER)

    @_('expr "." NAME')
    def expr(self, t):
        return Node('child', t.expr, t.NAME)
