import sys
sys.path.append((__file__.rstrip('/main.py') + '/src').lstrip('/'))

import parse
import runner
import errors

def getline():
    try:
        line = input('> ')
        return line
    except KeyboardInterrupt:
        print()
        return getline()
    except EOFError:
        sys.exit(0)

if sys.argv[1:]:

    l = parse.Lexer()
    p = parse.Parser()

    code = open(sys.argv[1]).read()

    tree = p.parse(l.tokenize(code))
    runner.run(tree)
else:
    print('Quill v 1.0')
    errors.setno()

    l = parse.Lexer()
    p = parse.Parser()

    program = runner.Program(parse.Node('program'))
    while True:
        code = getline()
        tree = p.parse(l.tokenize(code))
        program.ast = tree
        val = program.run()
        if val:
            program.print(val)
