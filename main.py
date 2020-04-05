# from Cython.Build import cythonize
# from distutils.core import setup
import sys

sys.path.append('./src')

import parse
import runner

# modules = ['src/data.pyx']
# setup(ext_modules = cythonize(modules))

l = parse.Lexer()
p = parse.Parser()

code = open(sys.argv[1]).read()

tree = p.parse(l.tokenize(code))
runner.run(tree)