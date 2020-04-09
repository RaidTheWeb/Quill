import sys
sys.path.append('./src')

import parse
import runner
import errors

l = parse.Lexer()
p = parse.Parser()

if sys.argv[1:]:
	code = open(sys.argv[1]).read()

	tree = p.parse(l.tokenize(code))
	runner.run(tree)
else:
	errors.setno()
	program = runner.Program(parse.Node('program'))
	while True:
		code = input('> ')
		tree = p.parse(l.tokenize(code))
		program.ast = tree
		val = program.run()
		if val:
			program.print(val)