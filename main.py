from Cython.Build import cythonize
from distutils.core import setup

modules = ['data.pyx']

setup(ext_modules = cythonize(modules))

import sys
sys.path.append('./src')

import parse
import runner

l = parse.Lexer()
p = parse.Parser()

code = open(sys.argv[1]).read()

tree = p.parse(l.tokenize(code))
runner.run(tree)