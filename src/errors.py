import sys

def error(msg):
	print(f'\033[0;31mError: {msg}\033[0;0m', file=sys.stderr)
	sys.exit(1)

def noexit(msg):
    print(f'\033[0;31mError: {msg}\033[0;0m', file=sys.stderr)

def setno():
    global error
    error = noexit
