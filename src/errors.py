import sys

def error(msg):
	print(f'\033[0;31mError: {msg}\033[0;0m', file=sys.stderr)
	sys.exit(1)